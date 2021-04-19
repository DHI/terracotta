

import { FeatureDataset } from "../../map/types"

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

export type ResponseMetadata200 = {
    keys: Record<string, string>,
    bounds: [number, number, number, number],
    convex_hull: FeatureDataset,
    valid_percentage: number,
    range: [ number, number ],
    mean: number,
    stdev: number,
    percentiles: number[],
    metadata: Record<string, string>
}

export type ResponseMetadata404 = {
    message: string
}

export type ResponseMetadata = ResponseMetadata200 | ResponseMetadata404

const getData = async (url: string): Promise< ResponseKeys | ResponseDatasets | ResponseMetadata | undefined> => {

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