import Mutex from './mutex.ts'

const mutex = new Mutex();
let num = 0
for (let index = 0; index < 500; index++) {
    
    let job = async () => {
        await mutex.acquire()

        await sleep(300)
        num++
        console.log(num)
        mutex.release()
    }
    job()
    
}
await sleep(1000)

function sleep(ms:number) {
    return new Promise(resolve => setTimeout(resolve, ms));
}