import { createContext } from 'react'
import { Viewport } from "./map/types"
import { FeatureDataset } from "./map/types"
import { ResponseMetadata200 } from "./common/data/getData"
import { Colormap } from "./colormap/colormaps"

export type RGBValue = {
	range: number[],
	band: string
}

export type activeRGBSelectorRange = {
	R: RGBValue,
	G: RGBValue,
	B: RGBValue,
	[key: string]: RGBValue
}

interface AppContextValues {
	state: {
        viewport: Viewport,
        isOpticalBasemap: boolean,
		hostname: string | undefined,
		keys: string[] | undefined,
		hoveredDataset: FeatureDataset | undefined,
		datasets: undefined | ResponseMetadata200[],
		activeDataset: undefined | number,
		selectedDatasetRasterUrl: string | undefined,
		page: number,
		limit: number,
		colormap: Colormap,
		activeSinglebandRange: [ number, number ] | undefined,
		activeRGB: activeRGBSelectorRange | undefined,
		activeEndpoint: string,
		datasetBands: string[] | undefined
	},
	actions: {
		setIsOpticalBasemap: Function,
        setViewport: Function,
		setKeys: Function,
		setHoveredDataset: Function,
		setDatasets: Function,
		setActiveDataset: Function,
		setSelectedDatasetRasterUrl: Function,
		setPage: Function,
		setLimit: Function,
		setColormap: Function,
		setActiveSinglebandRange: Function,
		setActiveEndpoint: Function,
		setActiveRGB: Function,
		setDatasetBands: Function
	},
}

type Context = AppContextValues

const AppContext = createContext<Context>(null as any)

export default AppContext
