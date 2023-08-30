import { Dispatch, SetStateAction, createContext } from 'react'
import { Map } from 'mapbox-gl'
import { FeatureDataset } from './map/types'
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
		mapRef: Map | undefined
	}
	actions: {
		setIsOpticalBasemap: Dispatch<SetStateAction<boolean>>
		setKeys: Dispatch<SetStateAction<KeyItem[] | undefined>>
		setHoveredDataset: Dispatch<SetStateAction<FeatureDataset | undefined>>
		setDatasets: Dispatch<SetStateAction<ResponseMetadata200[] | undefined>>
		setActiveDataset: Dispatch<SetStateAction<undefined | number>>
		setSelectedDatasetRasterUrl: Dispatch<SetStateAction<string | undefined>>
		setPage: Dispatch<SetStateAction<number>>
		setLimit: Dispatch<SetStateAction<number>>
		setColormap: Dispatch<SetStateAction<Colormap>>
		setActiveSinglebandRange: Dispatch<
			SetStateAction<[number, number] | undefined>
		>
		setActiveEndpoint: Dispatch<SetStateAction<string>>
		setActiveRGB: Dispatch<SetStateAction<ActiveRGBSelectorRange | undefined>>
		setDatasetBands: Dispatch<SetStateAction<string[] | undefined>>
		setMapRef: Dispatch<SetStateAction<mapboxgl.Map | undefined>>
	}
}

type Context = AppContextValues

const AppContext = createContext<Context>(null as any)

export default AppContext
