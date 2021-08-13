import { CqMessageEvent, QuickReply } from '../deps.ts'

/** 获取一张随机猫猫图 */
export async function cat(msg: CqMessageEvent, command: string): Promise<QuickReply> {
    let url = await cat_pic_url()
    return msg.quick_reply('[CQ:image,file=' + url + ']')
}

/** 获取一张随机狗狗图 */
export async function dog(msg: CqMessageEvent, command: string): Promise<QuickReply> {
    let url = await dog_pic_url()
    return msg.quick_reply('[CQ:image,file=' + url + ']')
}


export async function cat_pic_url(): Promise<string> {
    type catapi = [{
        breeds: any[];
        id: string;
        url: string;
        width: number;
        height: number;
    }]
    let res = await fetch("https://api.thecatapi.com/v1/images/search")
    let api: catapi = await res.json()
    return api[0].url
}

export async function dog_pic_url(): Promise<string> {
    type dogapi = {
        message: string
        status: string
    }

    let res = await fetch('https://dog.ceo/api/breeds/image/random')
    let api: dogapi = await res.json()
    return api.message
}