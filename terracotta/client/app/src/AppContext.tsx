import { Dispatch, SetStateAction, createContext } from 'react'
import { Viewport, FeatureDataset } from './map/types'
import { ResponseMetadata200, KeyItem } from './common/data/getData'
import { Colormap } from './colormap/colormaps'

export type RGBValue = {
	range: number[] | undefined
	band: string | undefined
}

export type ActiveRGBSelectorRange = {
	R: RGBValue
	G: RGBValue
	B: RGBValue
	[key: string]: RGBValue
}

interface AppContextValues {
	state: {
		viewport: Viewport
		isOpticalBasemap: boolean
		hostname: string | undefined
		keys: KeyItem[] | undefined
		hoveredDataset: FeatureDataset | undefined
		datasets: undefined | ResponseMetadata200[]
		activeDataset: undefined | number
		selectedDatasetRasterUrl: string | undefined
		page: number
		limit: number
		colormap: Colormap
		activeSinglebandRange: [number, number] | undefined
		activeRGB: ActiveRGBSelectorRange | undefined
		activeEndpoint: string
		datasetBands: string[] | undefined
	}
	actions: {
		setIsOpticalBasemap: any // Dispatch<SetStateAction<boolean>>
		setViewport: any // Dispatch<SetStateAction<Viewport>>
		setKeys: any // Dispatch<SetStateAction<KeyItem[] | undefined>>
		setHoveredDataset: any // Dispatch<SetStateAction<FeatureDataset | undefined>>
		setDatasets: any // Dispatch<SetStateAction<any>>
		setActiveDataset: any // Dispatch<SetStateAction<undefined | number>>
		setSelectedDatasetRasterUrl: any // Dispatch<SetStateAction<string | undefined>>
		setPage: any // Dispatch<SetStateAction<number>>
		setLimit: any // Dispatch<SetStateAction<number>>
		setColormap: any // Dispatch<SetStateAction<Colormap>>
		setActiveSinglebandRange: any // Dispatch<SetStateAction<[number, number] | undefined>>
		setActiveEndpoint: any // Dispatch<SetStateAction<string>>
		setActiveRGB: any // Dispatch<SetStateAction<ActiveRGBSelectorRange | undefined>>
		setDatasetBands: any // Dispatch<SetStateAction<string[] | undefined>>
	}
}

type Context = AppContextValues

const AppContext = createContext<Context>(null as any)

export default AppContext
