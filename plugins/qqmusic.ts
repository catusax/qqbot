import { CqMessageEvent, QuickReply } from '../deps.ts'
import {find_first} from './utils.ts'

/** 获取搜索到的qq音乐的第一个id */
export default async function qqmusic(msg: CqMessageEvent, command: string): Promise<QuickReply> {
    let name = find_first(msg.message, /(?<=点歌 ).*/gm)
    name = name.trim()
    try {
      let music_id = await qmusic(name)
      return msg.quick_reply('[CQ:music,type=qq,id=' + music_id + ']')
    } catch (e) {
      return msg.quick_reply(e.message)
    }
  }

async function qmusic(word: string): Promise<string> {
    let qmusicapi = 'https://api.qq.jsososo.com/search/quick?key=' //第三方qq音乐api
    // let musicuri = 'https://i.y.qq.com/v8/playsong.html?songid='
    let query = qmusicapi + word
  
    try {
      let resp = await (await fetch(query, {
        "credentials": "omit",
        "headers": {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
          "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
          "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
          "Upgrade-Insecure-Requests": "1",
          "Pragma": "no-cache",
          "Cache-Control": "no-cache"
        },
        "method": "GET",
        "mode": "cors"
      })).json()
  
      // console.log(resp)
      if (resp.result == 100) {
        if (resp.data.song.count != 0) {
          return resp.data.song.itemlist[0].id
        } else {
          throw Error('搜不到歌曲')
        }
      } else {
        throw Error('查询api出错：' + resp.result)
      }
    } catch (error) {
      throw error
    }
  }