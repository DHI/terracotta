import React, { FC, useState, useEffect, useContext, Fragment } from 'react'
import {
	Table,
	TableBody,
	TableCell,
	TableContainer,
	TableHead,
	TableRow as MuiTableRow,
	Typography,
	Box,
} from '@mui/material'
import { makeStyles } from '@mui/material/styles'
import AppContext, { ActiveRGBSelectorRange } from '../AppContext'
import getData, {
	ResponseDatasets,
	DatasetItem,
	ResponseMetadata200,
	ResponseKeys,
	KeyItem,
} from '../common/data/getData'
import SidebarItemWrapper from '../sidebar/SidebarItemWrapper'
import TablePagination from './TablePagination'
import TableRow from './TableRow'
import DatasetsForm from './DatasetsForm'
import DatasetPreview from './DatasetPreview'
import DatasetsColormap from '../colormap/DatasetsColormap'
import { defaultRGB } from '../App'

const styles = {
	wrapper: {
		m: 2,
		pb: 2,
		backgroundColor: '#FFFFFF',
		borderBottom: '1px solid #86A2B3',
	},
	table: {
		marginTop: '1rem',
		width: '100%',
		overflowX: 'auto',
		overflowY: 'auto',
		maxHeight: 515,
	},
	tableHeadTypography: {
		fontWeight: 'bold',
	},
	tableCell: {
		p: 1,
	},
}

interface Props {
	host: string
}

const limitOptions = [15, 25, 50, 100]

const SidebarDatasetsItem: FC<Props> = ({ host }) => {
	const {
		state: {
			keys,
			datasets,
			activeDataset,
			limit,
			page,
			activeSinglebandRange,
			colormap,
			activeEndpoint,
			activeRGB,
			selectedDatasetRasterUrl,
		},
		actions: {
			setKeys,
			setHoveredDataset,
			setDatasets,
			setActiveDataset,
			setSelectedDatasetRasterUrl,
			setLimit,
			setPage,
			setActiveSinglebandRange,
			setActiveRGB,
			setDatasetBands,
		},
	} = useContext(AppContext)

	const [queryFields, setQueryFields] = useState<string | undefined>(undefined)
	const [isLoading, setIsLoading] = useState<boolean>(true)

	const getDatasets = async (
		theHost: string,
		pageRef: number,
		limitRef: number,
		queryString = '',
	) => {
		const response = await getData(
			`${theHost}/datasets?limit=${limitRef}&page=${pageRef}${queryString}`,
		)
		const datasetsResponse = response as ResponseDatasets | undefined

		if (
			datasetsResponse &&
			datasetsResponse.datasets &&
			Array.isArray(datasetsResponse.datasets)
		) {
			if (datasetsResponse.datasets[0]) {
				const metadataResponsesPreFetch: unknown =
					datasetsResponse.datasets.map(async (dataset: DatasetItem) => {
						const buildMetadataUrl = Object.keys(dataset)
							.map((keyItem: string) => `/${dataset[keyItem]}`)
							.join('')
						const preFetchData = await fetch(
							`${host}/metadata${buildMetadataUrl}`,
						)
						return preFetchData.json()
					})

				const metadataResponses = await Promise.all(
					metadataResponsesPreFetch as Iterable<unknown>,
				)
				const typedMetadataResponses =
					metadataResponses as ResponseMetadata200[]
				setDatasets(typedMetadataResponses)
			} else {
				setDatasets(datasetsResponse.datasets)
			}
		}

		setIsLoading(false)
	}

	const getKeys = async (theHost: string) => {
		const response = await getData(`${theHost}/keys`)
		const keysReponse = response as ResponseKeys | undefined

		if (keysReponse && keysReponse.keys && Array.isArray(keysReponse.keys)) {
			keysReponse.keys = keysReponse.keys.map((item: KeyItem) => ({
				...item,
				key: item.key[0].toUpperCase() + item.key.substring(1, item.key.length),
			}))
			setKeys(keysReponse.keys)
		}
	}

	const onHandleRow = (index: number) => {
		const actualIndex = page * limit + index
		setActiveRGB(defaultRGB)
		if (activeDataset === actualIndex) {
			setActiveDataset(undefined)
			setSelectedDatasetRasterUrl(undefined)
			setActiveSinglebandRange(undefined)
		} else {
			const dataset = datasets?.[index]
			setActiveDataset(actualIndex)

			if (dataset) {
				const { percentiles } = dataset
				const validRange = [percentiles[4], percentiles[94]]
				setActiveSinglebandRange(validRange)
			}
		}
	}

	const onSubmitFields = (queryString: string) => {
		setQueryFields(queryString)
		setPage(0)
		setActiveDataset(undefined)
		setSelectedDatasetRasterUrl(undefined)
	}

	useEffect(() => {
		setIsLoading(true)
		void getKeys(host)
		void getDatasets(host, page, limit, queryFields)
	}, [host, page, limit, queryFields])

	const onGetRGBBands = async (dataset: ResponseMetadata200) => {
		const noBandKeysURL = `${host}/datasets?${Object.keys(dataset.keys)
			.map((item: string) =>
				item !== 'band' ? `${item}=${dataset.keys[item]}&` : '',
			)
			.join('')}`

		const response = (await getData(noBandKeysURL)) as ResponseDatasets

		if (response?.datasets && activeRGB) {
			const { datasets: theDatasets } = response
			const bands = theDatasets.map((ds: DatasetItem) => ds.band)

			setActiveRGB((activeRGBLocal: ActiveRGBSelectorRange) =>
				Object.keys(activeRGBLocal).reduce((acc: any, colorString: string) => {
					const { percentiles } = dataset
					const validRange = [percentiles[4], percentiles[94]]

					acc[colorString] = {
						...activeRGBLocal[colorString],
						range: validRange,
					}

					return acc
				}, {}),
			)

			setDatasetBands(bands)
		}
	}

	useEffect(() => {
		if (activeDataset !== undefined && datasets && activeSinglebandRange) {
			setSelectedDatasetRasterUrl(undefined)
			const dataset = datasets[activeDataset - page * limit]
			const keysRasterUrl = `${Object.keys(dataset.keys)
				.map((keyItem: string) => `/${dataset.keys[keyItem]}`)
				.join('')}/{z}/{x}/{y}.png`

			if (activeEndpoint === 'singleband') {
				// setActiveRGB(defaultRGB)
				const buildRasterUrl = `${host}/${activeEndpoint}${keysRasterUrl}?colormap=${colormap.id}&stretch_range=[${activeSinglebandRange}]`
				setSelectedDatasetRasterUrl(buildRasterUrl)
			}

			if (activeEndpoint === 'rgb') {
				void onGetRGBBands(dataset)
			}
		}
	}, [activeSinglebandRange, colormap, activeDataset, activeEndpoint])

	useEffect(() => {
		if (
			activeRGB &&
			activeEndpoint === 'rgb' &&
			datasets &&
			activeDataset !== undefined
		) {
			const dataset = datasets[activeDataset - page * limit]
			const hasValueForBand = Object.keys(activeRGB).every(
				(colorObj) => activeRGB[colorObj].band,
			)
			const hasValueForRange = Object.keys(activeRGB).every(
				(colorObj) => activeRGB[colorObj].range,
			)

			if (hasValueForBand && hasValueForRange && dataset !== undefined) {
				const lastKey = Object.keys(dataset.keys)[
					Object.keys(dataset.keys).length - 1
				]
				const keysRasterUrl = `${Object.keys(dataset.keys)
					.map((keyItem: string) =>
						keyItem !== lastKey ? `/${dataset.keys[keyItem]}` : '',
					)
					.join('')}/{z}/{x}/{y}.png`
				const rgbParams = Object.keys(activeRGB)
					.map(
						(keyItem: string) =>
							`${keyItem.toLowerCase()}=${
								activeRGB[keyItem].band
							}&${keyItem.toLowerCase()}_range=[${activeRGB[keyItem].range}]&`,
					)
					.join('')
				const buildRasterUrl = `${host}/${activeEndpoint}${keysRasterUrl}?${rgbParams}`
				setSelectedDatasetRasterUrl(buildRasterUrl)
			}
		}
	}, [activeRGB, activeEndpoint, activeDataset, datasets])

	return (
		<SidebarItemWrapper isLoading={isLoading} title="Search for datasets">
			<Box>
				{keys && <DatasetsForm keys={keys} onSubmitFields={onSubmitFields} />}
			</Box>
			<DatasetsColormap />
			<Box sx={styles.table}>
				<TableContainer onMouseLeave={() => setHoveredDataset(undefined)}>
					<Table
						aria-label="enhanced table"
						aria-labelledby="tableTitle"
						size="small" // medium
					>
						<TableHead>
							<MuiTableRow>
								<TableCell sx={styles.tableCell} />
								{keys &&
									keys.map((datasetKey: KeyItem, i: number) => (
										<TableCell
											key={`dataset-key-head-${i}`}
											sx={styles.tableCell}
										>
											<Typography
												color="primary"
												sx={styles.tableHeadTypography}
												variant="body2"
											>
												{datasetKey.key}
											</Typography>
										</TableCell>
									))}
							</MuiTableRow>
						</TableHead>
						<TableBody>
							{datasets &&
								datasets.map((dataset: ResponseMetadata200, i: number) => (
									<Fragment key={`dataset-${i}`}>
										<TableRow
											checked={page * limit + i === activeDataset}
											dataset={dataset.keys}
											keyVal={`dataset-${i}`}
											onClick={() => onHandleRow(i)}
											onMouseEnter={() =>
												setHoveredDataset(dataset.convex_hull)
											}
										/>
										<DatasetPreview
											activeDataset={activeDataset}
											dataset={dataset}
											datasetUrl={selectedDatasetRasterUrl}
											host={host}
											i={i}
											limit={limit}
											page={page}
										/>
									</Fragment>
								))}
						</TableBody>
					</Table>
				</TableContainer>
			</Box>
			<TablePagination
				disableNext={limit > (datasets?.length || 0)}
				options={limitOptions}
				page={page}
				value={limit}
				onGetPage={(val: number) => setPage(val)}
				onGetValue={(val: number) => setLimit(val)}
			/>
		</SidebarItemWrapper>
	)
}

export default SidebarDatasetsItem
