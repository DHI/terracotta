
export type KeyItem = {
    key: string
}

export type ResponseKeys = {
    keys: KeyItem[]
}

export type DatasetItem = Record<string, string>

export type ResponseDatasets = {
    page: number,
    limit: number,
    datasets: DatasetItem[]
}

const getData = async (url: string): Promise< ResponseKeys | ResponseDatasets | undefined> => {

    try{

        const data = await fetch(url);
        const json = await data.json();
        return json

    }catch(err){

        console.error(err)
        return undefined
    }

}

export default getData;