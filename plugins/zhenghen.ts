import { CqCode, CqMessageEvent, es_uri, QuickReply } from "../deps.ts";

export default async function zhengshen(
    msg: CqMessageEvent,
    command: string
): Promise<QuickReply> {
    // let keyword = find_first(msg.message, /(?<=搜索 ).*/gm);

    let cqcode = new CqCode(msg.message);

    let user = cqcode.at;

    if (user == 0) {
        msg.quick_reply("bad request");
    }

    try {
        let res = await searchUser(user);
        let cqcode = `${user} 一共在本群发言${res}次`;
        return msg.quick_reply(cqcode);
    } catch (error) {
        return msg.quick_reply("没有搜到！");
    }
}

export async function searchUser(user: number): Promise<number> {
    let resp = await fetch(es_uri + "_count", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: `{
        "query": {
            "bool": {
            "must": [
                {
                "match": {
                    "message": {
                    "sender_id": ${user}
                    }
                }
                }
            ]
            }
        }
    }`,
    });
    if (resp.status != 200) {
        throw "查询错误";
    } else {
        let json = await resp.json();
        return json.count;
    }
}
