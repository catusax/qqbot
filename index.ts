import { QBot, CqMessageEvent, CqCode, QuickReply } from './deps.ts'
import { ws_url } from './deps.ts'

import * as db from './db/db.ts'
import {plugins,at_plugins} from './plugins/mod.ts'


const bot = new QBot(ws_url)


/** at消息的处理 */
async function regex_match_at(msg: CqMessageEvent, cqcode: CqCode) {

  for (const item of at_plugins) {
    if (item.regex.test(msg.message)) {
      // QPS限制
      let limit = await db.QPS_limit(msg, '*', 3)
      if (limit == 1) {
        bot.send(JSON.stringify(msg.quick_reply(`[CQ:at,qq=${msg.sender.user_id}] 一天到晚就知道BB，你BB个🔨`)))
        return
      }
      if (limit == 2) {
        // bot.send(JSON.stringify(msg.quick_reply(`[CQ:at,qq=${msg.sender.user_id}] 差不多得了😅`))) // TODO: 更多操作
        return
      }
      let resp = await item.handler(msg, msg.message)
      bot.send(JSON.stringify(resp))
      break
    }
  }
  // bot.send(msg.quick_reply('[CQ:image,file=https://http.cat/404]')) //404
}

/** 普通消息的处理(包含at消息) */
async function regex_match(msg: CqMessageEvent) {

  // console.log(msg.message)
  for (const item of plugins) {
    if (item.regex.test(msg.message)) {

      // QPS限制
      let limit = await db.QPS_limit(msg, '*', 3)
      if (limit == 1) {
        bot.send(JSON.stringify(msg.quick_reply(`[CQ:at,qq=${msg.sender.user_id}] 一天到晚就知道BB，你BB个🔨`)))
        return
      }
      if (limit == 2) {
        // bot.send(JSON.stringify(msg.quick_reply(`[CQ:at,qq=${msg.sender.user_id}] 差不多得了😅`))) // TODO: 更多操作
        return
      }

      // console.log(msg)
      let resp = await item.handler(msg, msg.message)
      await db.save_quick_reply_to_mongo_and_es(resp)
      bot.send(JSON.stringify(resp))
      break
    }
  }
  // bot.send(msg.quick_reply('[CQ:image,file=https://http.cat/404]')) //404
}


bot.onmessage(db.save_to_mongo_and_es)

bot.onmessage(regex_match)
bot.on_at_message(regex_match_at)
bot.run()
