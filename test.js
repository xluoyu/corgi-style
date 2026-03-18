function myPromiseAll(list){
    return Promise((resolve, reject) => {
        if(!Array.isArray(list)){
            reject(new TypeError('arguments must be an array'))
        }

        if (list.length === 0){
            resolve([])
        }

        const res = []
        let count = 0
        list.forEach((item, index) => {
            item.then((val) => {
                res[index] = val
                count++
                if(count === list.length){
                    resolve(res)
                }
            }).catch((err) => {
                reject(err)
            })
        })
    })
}