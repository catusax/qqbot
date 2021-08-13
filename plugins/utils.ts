/**  查找匹配到的第一个字符串，没有则返回''*/
export function find_first(str:string,reg:RegExp|string):string {
  let find = str.match(reg)
  if (find == null){
    return ''
  }
  return find[0]
}