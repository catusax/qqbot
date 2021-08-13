import { CqMessageEvent, QuickReply } from '../deps.ts'

/** 获取毛泽东语录 */
export default async function mao(msg: CqMessageEvent, command: string): Promise<QuickReply> {
    return msg.quick_reply(await mao_quote())
}

async function mao_quote(): Promise<string> {
    type quote = {
        quote: string
        from: string
    }
    let quote: quote = await (await fetch("https://mao.coolrc.workers.dev/")).json()
    let res = quote.quote + '\n' + quote.from
    return res
}