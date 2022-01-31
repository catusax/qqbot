import { CqMessageEvent, QuickReply } from "../deps.ts";
import { find_first } from "./utils.ts";

export default async function searcKeyword(
  msg: CqMessageEvent,
  command: string
): Promise<QuickReply> {
  let keyword = find_first(msg.message, /(?<=搜索 ).*/gm);
  console.log(keyword);
  keyword = keyword.trim();
  try {
    let res = await searchKeyword(keyword);
    let cqcode = `${res.nickname} [${res.id}] 说<${keyword}>的次数最多，(可能)说了${res.times}次 `;
    return msg.quick_reply(cqcode);
  } catch (error) {
    return msg.quick_reply("没有搜到！");
  }
}

import { es_uri } from "../deps.ts";

export async function searchKeyword(keyword: string): Promise<result> {
  let resp = await fetch(es_uri + "_search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: `{
            "query": {
              "bool": {
                "must": [
                  {
                    "match_phrase_prefix": {
                      "message": {
                        "query": "${keyword}"
                      }
                    }
                  }
                ],
                "must_not": [
                    {
                      "term": {
                      "message":"搜索"
                      }
                  },
                  {
                    "match": {
                      "sender_id": "228901779"
                    }
                  }
                ]
              }
            },
            "from": 0,
            "size": 10,
            "aggs": {
              "group_by_name": {
                "terms": {
                  "field": "sender_id",
                  "size": 20,
                  "order": {
                    "amount": "desc"
                  }
                },
                "aggs": {
                  "amount": {
                    "value_count": {
                      "field": "unique_id"
                    }
                  }
                }
              }
            }
          }`,
  });
  if (resp.status != 200) {
    throw "查询错误";
  } else {
    let json = await resp.json();
    if (json.hits.total.value == 0) {
      throw "没有查询到";
    } else {
      let id = json.aggregations.group_by_name.buckets[0].key;
      let times = json.aggregations.group_by_name.buckets[0].amount.value;

      let nickname;
      try {
        nickname = await getQNickname(id);
      } catch (error) {
        nickname = null;
      }

      return {
        id: id,
        times,
        nickname,
      };
    }
  }
}

type result = {
  id: number;
  times: number;
  nickname: string | null;
};

export async function getQNickname(id: number) {
  let resp = await fetch(es_uri + "_search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: `
        {
            "size": 1,
            "query": {
              "bool": {
                "must": {
                  "match": {
                    "sender_id": "${id}"
                  }
                },
                "must_not": {
                  "match": {
                    "sender": "${id}"
                  }
                }
              }
            },
            "sort": { "unique_id": { "order": "desc" }}
          }`,
  });

  if (resp.status != 200) {
    throw "查询错误";
  } else {
    let json = await resp.json();
    if (json.hits.total.value == 0) {
      throw "没有查询到";
    } else {
      let nickname = json.hits.hits[0]._source.sender;
      return nickname;
    }
  }
}

// let id = 1782536964

// console.log(await getQNickname(id))
