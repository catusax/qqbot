import { CqMessageEvent, QuickReply } from '../deps.ts'

/** 从360搜索里获取一张图片 */
export default async function search_360pic(msg: CqMessageEvent, command: string): Promise<QuickReply> {
    try {
        let url = await search_pic(command)
        return msg.quick_reply('[CQ:image,file=' + url + ']')

    } catch (error) {
        return msg.quick_reply('搜不到图片')
    }

}

async function search_pic(name: string):Promise<string> {
    let res:picResult = await (await fetch("https://image.so.com/j?keep=1&src=a_corr&q="+name)).json()
    if (res.total == 0) {
        throw new Error("搜不到图片");
        
    }
    let range = res.list.length>=20?20:res.list.length //从前十张里随机取
    let index =  Math.floor(Math.random()*range);
    return res.list[index].thumb
}

type PicList = {
    id: string;
    qqface_down_url: boolean;
    downurl: boolean;
    downurl_true: string;
    grpmd5: boolean;
    type: number;
    src: string;
    color: number;
    index: number;
    title: string;
    litetitle: string;
    width: string;
    height: string;
    imgsize: string;
    imgtype: string;
    key: string;
    dspurl: string;
    link: string;
    source: number;
    img: string;
    thumb_bak: string;
    thumb: string;
    _thumb_bak: string;
    _thumb: string;
    imgkey: string;
    thumbWidth: number;
    dsptime: string;
    thumbHeight: number;
    grpcnt: string;
    fixedSize: boolean;
    fnum: string;
    comm_purl: string;
}
type picResult = {
    total: number;
    end: boolean;
    sid: string;
    ran: number;
    ras: number;
    cuben: number;
    manun: number;
    pornn: number;
    kn: number;
    cn: number;
    gn: number;
    ps: number;
    pc: number;
    adstar: number;
    lastindex: number;
    ceg: boolean;
    list: PicList[];
    boxresult: undefined;
    wordguess: undefined;
    prevsn: number;
}