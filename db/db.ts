import { CqCode, CqMessageEvent, QuickReply } from "../deps.ts";
import { MongoClient } from '../deps.ts';
import { es_uri, mongo } from '../deps.ts'
import Mutex from './mutex.ts'

const dbclient = new MongoClient();
await dbclient.connect(mongo);
const db_col = dbclient.database("chatlog").collection("chat_message")


class IdGenerator {
    id: Map<string, number>
    locks: any = {} //不同key对应不同锁

    constructor() {
        this.id = new Map<string, number>()
        // this.locks = new Map<string, Mutex>()
    }

    async getMaxId(key: string): Promise<number> {
        if (this.locks[key] == undefined) {
            this.locks[key] = new Mutex()
        }
        await this.locks[key].acquire()

        const option = {
            projection: { _id: 0, unique_id: 1, message: 1 },
        }
        let num = await db_col.find({ unique_tag: key }, option).sort({ unique_id: -1 }).limit(1).toArray() as { unique_id: number, message: string }[]
        let id
        if (num.length != 1) {
            id = 0
        } else {
            id = num[0].unique_id
        }
        this.locks[key].release()
        return id
    }

    // //旧版 使用了group
    // static async new() {
    //     let resp = await db_col.aggregate([
    //         { $group: { _id: null, max: { $max: "$uniqueid" } } },
    //     ]).toArray() as { _id: string, max: number }[]
    //     let id = 0
    //     if (resp.length != 0) {
    //         id = Number(resp[0].max)
    //     }
    //     return new IdGenerator(id)
    // }

    async getid(key: string): Promise<number> {
        if (this.id.has(key)) {
            let num = (this.id.get(key) || 0) + 1
            this.id.set(key, num)
            return num
        } else {
            let num = await this.getMaxId(key)
            num++
            this.id.set(key, num)
            return num
        }
    }
}

export const id = new IdGenerator()

export async function save_to_mongo(data: any) {
    let resp = await db_col.insertOne(data)

    // console.log(resp)
}

export async function save_to_es(data: any) {
    let resp = await fetch(es_uri+'_doc', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    if (resp.status == 201) {
        //   console.log(data)
    } else {
        console.log(await resp.text())
    }
}

/** 把收到的消息保存到mongo和es */
export async function save_to_mongo_and_es(msg: CqMessageEvent) {
    if (msg.post_type == "message") {
        let unique_tag = msg.group_id ? 'group' + msg.group_id : 'private' + msg.sender.user_id //标记所属会话
        let nickname = msg.group_id ? msg.sender.card || msg.sender.nickname || msg.sender.name : msg.sender.nickname  // 名片/昵称/匿名名称

        let cqcode = new CqCode(msg.message)

        let data = {
            "unique_id": await id.getid(unique_tag),
            "time": msg.time,
            "message_id": msg.message_id,
            "sender_id": msg.sender.user_id,
            "message_type": msg.message_type,
            "sub_type": msg.sub_type,
            "sender": nickname || '',
            "message": cqcode.message,
            "raw_message": (msg.message == cqcode.message) ? '' : msg.message, //如果有cq码就保存下原数据
            "group_id": msg.group_id || null,
            "unique_tag": unique_tag
        }
        console.log(data.sender, ':', data.message)
        // console.log(data.unique_tag, ':', data.unique_id)
        await save_to_es(data)
        await save_to_mongo(data)
    }
}

/** 把bot的返回消息保存到mongo和es */
export async function save_quick_reply_to_mongo_and_es(reply: QuickReply) {
    let msg = reply.params!.context
    if (msg.post_type == "message") {
        let unique_tag = msg.group_id ? 'group' + msg.group_id : 'private' + msg.sender.user_id //标记所属会话

        let cqcode = new CqCode(reply.echo || "")

        let data = {
            "unique_id": await id.getid(unique_tag),
            "time": Math.floor(Date.now() / 1000),
            "message_id": null, //不知道id
            "sender_id": msg.self_id,
            "message_type": msg.message_type,
            "sub_type": msg.sub_type,
            "sender": '宋江',
            "message": cqcode.message,
            "raw_message": (reply.echo.trim() == cqcode.message.trim()) ? '' : reply.echo,
            "group_id": msg.group_id || null,
            "unique_tag": unique_tag
        }
        await save_to_es(data)
        await save_to_mongo(data)
    }
}


const db_limit = dbclient.database("chatlog").collection("limit")

/** 利用mongo的缓存限制QPS
 * @param command 使用的命令，使用'*'表示对所有命令限制
 * @param limit 每分钟限制次数
 * @returns 返回0说明没超出限制 ,1超出限制，2超出限制+2
 */
export async function QPS_limit(msg: CqMessageEvent, command: string, limit: number) {
    if (msg.group_id) {
        let user = await db_limit.find({ id: msg.sender.user_id, command: command }).toArray() as limit[]

        let lim: limit = {
            createdAt: new Date(),
            id: msg.sender.user_id,
            command: command,
            group: msg.group_id
        }
        db_limit.insert(lim)
        let times = user.length
        if (times <= limit) {
            return 0
        } else {
            if (times >= limit + 2)
                return 2
            return 1
        }
    }
    return 0
}

type limit = {
    createdAt: Date
    id: number
    command: string
    group: number
}

// 测试
// const msg = new CqMessageEvent({
// group_id: 123345,
// sender:{
//     user_id:178825
// }
// })

// let is_ok = await QPS_limit(msg,"test",2)
// console.log(is_ok)