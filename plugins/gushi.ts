import { CqMessageEvent, QuickReply } from '../deps.ts'

/** 获取一句古诗 */
export default async function gushi(msg: CqMessageEvent, command: string): Promise<QuickReply> {
    return msg.quick_reply(await getgushi())
  }

/** 获取一句古诗 */
async function getgushi(): Promise<string> {
    interface gushiapi {
      status: string;
      data: Data;
      token: string;
      ipAddress: string;
      warning: null;
    }
  
    interface Data {
      id: string;
      content: string;
      popularity: number;
      origin: Origin;
      matchTags: string[];
      recommendedReason: string;
      cacheAt: Date;
    }
  
    interface Origin {
      title: string;
      dynasty: string;
      author: string;
      content: string[];
      translate: null;
    }
    let res = await fetch("https://v2.jinrishici.com/one.json?client=browser-sdk/1.2&X-User-Token=5BBmONtAj6%2FxYCUcoUSWfQb0HbRir%2FEX")
    let gushi: gushiapi = await res.json()
  
    let poetry = gushi.data.origin.title + '\n' + gushi.data.origin.author
    gushi.data.origin.content.forEach(elem => {
      poetry += '\n' + elem
    })
  
    return poetry
  }