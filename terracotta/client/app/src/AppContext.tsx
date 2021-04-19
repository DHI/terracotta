import { createContext } from 'react'
import { Viewport } from "./map/types"
import { FeatureDataset } from "./map/types"
import { ResponseMetadata200 } from "./common/data/getData"

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
		limit: number
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
		setLimit: Function
	},
}

type Context = AppContextValues

const AppContext = createContext<Context>(null as any)

export default AppContext
