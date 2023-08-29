import React, {
	useEffect,
	useState,
	FC,
	useContext,
	useRef,
	RefObject,
	ReactNode,
} from 'react'
import { Map, Source, Layer } from 'react-map-gl'
import ZoomControl from './MapZoomControl'
import useIsMobileWidth from '../common/hooks/useIsMobileWidth'
import AppContext from '../AppContext'
import { Viewport } from './types'
import { regionPaintFill, regionPaintLine } from './geojsonStyles'

const accessToken =
	'pk.eyJ1Ijoiam9zbGRoaSIsImEiOiJja2d0ZjdzbXAwMXdxMnNwN2Jkb2NvbXJ3In0.SayFfMYF2huWsZckbqNqEw'

interface Props {
	host?: string
}

const LocalMap: FC<Props> = ({ host }) => {
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
	const basemap = isOpticalBasemap
		? 'mapbox://styles/mapbox/satellite-v9'
		: 'mapbox://styles/mapbox/light-v10'

	const mapRef: RefObject<HTMLDivElement> | null = useRef(null)

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
		if (activeDataset !== undefined && datasets) {
			const pageIndex = activeDataset - page * limit
			const currentBounds = datasets[pageIndex].bounds

			const formattedBounds: [[number, number], [number, number]] = [
				[currentBounds[0], currentBounds[1]],
				[currentBounds[2], currentBounds[3]],
			]

			if (formattedBounds[0][0] >= 89) {
				formattedBounds[0][0] = 89
			}
			if (formattedBounds[0][1] <= -89) {
				formattedBounds[0][1] = -89
			}
			if (formattedBounds[1][0] >= 179) {
				formattedBounds[1][0] = 179
			}
			if (formattedBounds[1][1] >= 89) {
				formattedBounds[0][0] = 89
			}

			if (mapRef.current !== null) {
				const mapHeight = mapRef.current?.scrollHeight
				const currentMapWidth = mapRef.current?.scrollWidth

				if (mapHeight && currentMapWidth) {
					/* TODO
					const viewportBounds = new WebMercatorViewport({
						width: currentMapWidth,
						height: mapHeight,
					}).fitBounds(formattedBounds, { padding: 40 });

					const boundsViewportToPass = {
						zoom: viewportBounds.zoom,
						latitude: viewportBounds.latitude,
						longitude: viewportBounds.longitude,
					};

					setViewport((newViewport: Viewport) => ({
						...newViewport,
						...boundsViewportToPass,
					}));
					*/
				}
			}
		}
	}, [activeDataset])

	return (
		<Map mapStyle={basemap} mapboxAccessToken={accessToken}>
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
		</Map>
	)
}

export default LocalMap
