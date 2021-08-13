import { CqMessageEvent, QuickReply } from '../deps.ts'

import mao from './mao.ts'
import gushi from './gushi.ts'
import qqmusic from './qqmusic.ts'
import { cat, dog } from './cat_dog.ts'
import search_360pic from './360pic.ts'
import searcKeyword from './es_search.ts'


async function help(msg: CqMessageEvent, command: string): Promise<QuickReply> {
    let help = `使用说明:
  [命令]`
    plugins.forEach(element => {
        if (element.descripion) {
            help += '\n  ' + element.descripion
        }
    });

    return msg.quick_reply(help)
}

async function nothing(msg: CqMessageEvent, command: string): Promise<QuickReply> {
    return msg.quick_reply(`at我干啥`)
}


type Plugin = {
    regex: RegExp
    handler: (msg: CqMessageEvent, command: string) => Promise<QuickReply>
    descripion: string | null
}

// 从上到下搜索，只执行第一个匹配到的正则
export const plugins: Plugin[] = [
    {
        regex: /^help/,
        handler: help,
        descripion: "help: 帮助文档"
    },
    {
        regex: /^点歌 \S+/,
        handler: qqmusic,
        descripion: "点歌 <关键词>: 点一首歌"
    },
    {
        regex: /^猫猫图/,
        handler: cat,
        descripion: "猫猫图: 一张随机猫猫图"
    },
    {
        regex: /^狗狗图/,
        handler: dog,
        descripion: "狗狗图: 一张随机狗狗图"
    },
    // {
    //   regex: /^.{1,5}图$/,
    //   handler: search_360pic,
    //   descripion: "xx图: 搜图"
    // },
    {
        regex: /^念诗/,
        handler: gushi,
        descripion: "念诗: 苟利国家生死以"
    },
    {
        regex: /^搜索 \S+/,
        handler: searcKeyword,
        descripion: "搜索：在群消息记录里搜索一条信息"
    },
    {
        regex: /(汉奸|日本人|外国人)/,
        handler: mao,
        descripion: null
    },
    {
        regex: /^教育狗汉奸/,
        handler: mao,
        descripion: "教育狗汉奸: 用正能量语录教育狗汉奸"
    }
]

export const at_plugins: Plugin[] = [
    {
        regex: /^$/,
        handler: nothing,
        descripion: null
    },
]