
type ResponseKeys = {
    keys: {
        key: string
    }
}
const getData = async (url: string): Promise< ResponseKeys | undefined> => {

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