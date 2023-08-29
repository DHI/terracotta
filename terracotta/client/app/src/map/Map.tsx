/* eslint-disable radar/cognitive-complexity */
import React, {
	useEffect,
	useState,
	FC,
	useContext,
	useRef,
	RefObject,
	ReactNode,
} from 'react'
import { Map as ReactMapGL, Source, Layer } from 'react-map-gl'
import { Map } from 'mapbox-gl'
import ZoomControl from './MapZoomControl'
import useIsMobileWidth from '../common/hooks/useIsMobileWidth'
import AppContext from '../AppContext'
import { Viewport } from './types'
import { regionPaintFill, regionPaintLine } from './geojsonStyles'

const accessToken =
	'pk.eyJ1Ijoiam9zbGRoaSIsImEiOiJja2d0ZjdzbXAwMXdxMnNwN2Jkb2NvbXJ3In0.SayFfMYF2huWsZckbqNqEw'

interface Props {
	host?: string
	width: number
}

const LocalMap: FC<Props> = ({ host, width }) => {
	const isMobile = useIsMobileWidth()
	const {
		state: {
			isOpticalBasemap,
			viewport,
			hoveredDataset,
			datasets,
			activeDataset,
			selectedDatasetRasterUrl,
			page,
			limit,
		},
		actions: { setViewport },
	} = useContext(AppContext)

	const [localViewport, setLocalViewport] = useState<Viewport | undefined>(
		undefined,
	)
	const [localRasterUrl, setLocalRasterUrl] = useState<undefined | string>(
		undefined,
	)

	const [mapRef, setMapRef] = useState<Map | undefined>(undefined)

	const basemap = isOpticalBasemap
		? 'mapbox://styles/mapbox/satellite-v9'
		: 'mapbox://styles/mapbox/light-v10'

	useEffect(() => {
		const { latitude, longitude, zoom } = viewport
		setLocalViewport({
			...{
				longitude,
				latitude,
				zoom,
				transitionDuration: 2000,
			},
		})
	}, [viewport])

	useEffect(() => {
		setLocalRasterUrl(undefined)
		setTimeout(() => {
			setLocalRasterUrl(selectedDatasetRasterUrl)
		}, 200)
	}, [selectedDatasetRasterUrl])

	useEffect(() => {
		if (activeDataset === undefined || datasets === undefined) {
			return
		}

		const pageIndex = activeDataset - page * limit
		const currentBounds = datasets[pageIndex].bounds

		mapRef?.fitBounds(currentBounds as [number, number], {
			padding: 40,
			duration: 4000,
		})
	}, [activeDataset])

	useEffect(() => {
		mapRef?.resize()
	}, [width])

	useEffect(() => {
		const handleResize = () => {
			mapRef?.resize()
		}

		window.addEventListener('resize', handleResize)

		return () => {
			window.removeEventListener('resize', handleResize)
		}
	}, [])

	return (
		<ReactMapGL
			attributionControl={false}
			initialViewState={{
				latitude: 30.62136584218745,
				longitude: 13.840430671501323,
				zoom: 0,
				bearing: 0,
				pitch: 0,
				padding: {
					top: 0,
					bottom: 0,
					left: 0,
					right: 0,
				},
			}}
			mapStyle={basemap}
			mapboxAccessToken={accessToken}
			ref={(ref) => ref && setMapRef(ref as any)}
			style={{ width: window.innerWidth - width, height: '100%' }}
		>
			{!isMobile && <ZoomControl />}
			{hoveredDataset && (
				<Source data={hoveredDataset} type="geojson">
					<Layer
						id="hovered-dataset-fill"
						paint={regionPaintFill}
						type="fill"
					/>
					<Layer
						id="hovered-dataset-line"
						paint={regionPaintLine}
						type="line"
					/>
				</Source>
			)}
			{localRasterUrl && (
				<Source
					id="dataset_raster"
					tileSize={256}
					tiles={[localRasterUrl]}
					type="raster"
				>
					<Layer
						id="selected-dataset-raster"
						paint={{}}
						source="dataset_raster"
						type="raster"
					/>
				</Source>
			)}
		</ReactMapGL>
	)
}

export default LocalMap
