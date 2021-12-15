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
} from '@material-ui/core'
import AppContext, { activeRGBSelectorRange } from "../AppContext"
import { makeStyles } from '@material-ui/core/styles'
import
    getData,
    {
        ResponseDatasets,
        DatasetItem,
        ResponseMetadata200,
        ResponseKeys,
        KeyItem
} from "../common/data/getData"
import SidebarItemWrapper from "../sidebar/SidebarItemWrapper"
import TablePagination from "./TablePagination"
import TableRow from "./TableRow"
import DatasetsForm from "./DatasetsForm"
import DatasetPreview from "./DatasetPreview"
import DatasetsColormap from "../colormap/DatasetsColormap"
import { defaultRGB } from "../App"


const useStyles = makeStyles(() => ({
    wrapper: {
		margin: 16,
        paddingBottom: 16,
		backgroundColor: '#FFFFFF',
		borderBottom: '1px solid #86A2B3',
	},
    table: {
        marginTop: '1rem',
        width: "100%",
        overflowX: 'auto',
        overflowY: 'auto',
        maxHeight: 515
    },
    tableHeadTypography: {
        fontWeight: 'bold',
    },
    tableCell: {
        padding: 6
    },

}))

interface Props {
    host: string
}

const limitOptions = [ 15, 25, 50, 100 ]

const SidebarDatasetsItem: FC<Props> = ({
    host
}) => {
    const classes = useStyles()
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
            selectedDatasetRasterUrl
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
            setDatasetBands
        }
    } = useContext(AppContext)

    const [ queryFields, setQueryFields ] = useState<string | undefined>(undefined)
    const [ isLoading, setIsLoading ] = useState<boolean>(true)

    const getDatasets = async (host: string, pageRef: number, limitRef: number, queryString: string = '') => {

        const response = await getData(`${host}/datasets?limit=${limitRef}&page=${pageRef}${queryString}`)
        const datasetsResponse = response as ResponseDatasets | undefined
        if(datasetsResponse && datasetsResponse.hasOwnProperty('datasets') && Array.isArray(datasetsResponse.datasets)){

            if(datasetsResponse.datasets[0]){

                const metadataResponsesPreFetch: unknown = datasetsResponse.datasets.map(
                    async (dataset: DatasetItem) => {
                        const buildMetadataUrl = Object.keys(dataset).map((keyItem: string) => `/${dataset[keyItem]}`).join('')
                        const preFetchData = await fetch(`${host}/metadata${buildMetadataUrl}`)
                        return preFetchData.json()
                    })

                    const metadataResponses = await Promise.all(metadataResponsesPreFetch as Iterable<unknown>)
                    const typedMetadataResponses = metadataResponses as ResponseMetadata200[]
                    setDatasets(typedMetadataResponses)

            }else{

                setDatasets(datasetsResponse.datasets)

            }

        }

        setIsLoading(false)
    }

    const getKeys = async (host: string) => {

        const response = await getData(`${host}/keys`)
        let keysReponse = response as ResponseKeys | undefined

        if(keysReponse && keysReponse.hasOwnProperty('keys') && Array.isArray(keysReponse.keys)){

            keysReponse.keys = keysReponse.keys.map((item: KeyItem) => ({ ...item, key: item.key[0].toUpperCase() + item.key.substring(1, item.key.length ) }))
            setKeys(keysReponse.keys)

        }


    }

    const onHandleRow = (index: number) => {

        const actualIndex = page * limit + index;
        setActiveRGB(defaultRGB)
        if(activeDataset === actualIndex){

            setActiveDataset(undefined)
            setSelectedDatasetRasterUrl(undefined)
            setActiveSinglebandRange(undefined)

        }else{

            const dataset = datasets?.[index]
            setActiveDataset(actualIndex)

            if(dataset){

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

    }, [host, page, limit, queryFields]) // eslint-disable-line react-hooks/exhaustive-deps

    const onGetRGBBands = async (dataset: ResponseMetadata200) => {
        const noBandKeysURL = `${host}/datasets?` + Object.keys(dataset.keys).map((item: string) => item !== 'band' ? `${item}=${dataset.keys[item]}&` : '' ).join('')
        const response = await getData(noBandKeysURL) as ResponseDatasets

        if(response?.datasets && activeRGB){

            const { datasets } = response
            const bands = datasets.map((dataset: DatasetItem) => dataset.band)

            setActiveRGB((activeRGBLocal: activeRGBSelectorRange) =>
                Object.keys(activeRGBLocal).reduce((acc: any, colorString: string) => {

                    const { percentiles } = dataset
                    const validRange = [ percentiles[4], percentiles[94] ]

                    acc[colorString] = { ...activeRGBLocal[colorString], range: validRange }

                    return acc

                }, {}))

            setDatasetBands(bands)

        }
    }


    useEffect(() => {

        if(activeDataset !== undefined && datasets && activeSinglebandRange){

            setSelectedDatasetRasterUrl(undefined)
            const dataset = datasets[activeDataset - page * limit]
            const keysRasterUrl = Object.keys(dataset.keys).map((keyItem: string) => `/${dataset.keys[keyItem]}`).join('') + '/{z}/{x}/{y}.png'

            if(activeEndpoint === 'singleband'){

                // setActiveRGB(defaultRGB)
                const buildRasterUrl = `${host}/${activeEndpoint}${keysRasterUrl}?colormap=${colormap.id}&stretch_range=[${activeSinglebandRange}]`
                setSelectedDatasetRasterUrl(buildRasterUrl)

            }

            if(activeEndpoint === 'rgb'){
               void onGetRGBBands(dataset)
            }
        }

    }, [activeSinglebandRange, colormap, activeDataset, activeEndpoint])  // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {

        if(activeRGB && activeEndpoint === 'rgb' && datasets && activeDataset !== undefined){

            const dataset = datasets[activeDataset - page * limit]
            const hasValueForBand = Object.keys(activeRGB).every((colorObj) => activeRGB[colorObj].band)
            const hasValueForRange = Object.keys(activeRGB).every((colorObj) => activeRGB[colorObj].range)

            if(hasValueForBand && hasValueForRange && dataset !== undefined){

                const lastKey = Object.keys(dataset.keys)[Object.keys(dataset.keys).length - 1]
                const keysRasterUrl = Object.keys(dataset.keys).map((keyItem: string) => keyItem !== lastKey ? `/${dataset.keys[keyItem]}` : '').join('') + '/{z}/{x}/{y}.png'
                const rgbParams = Object.keys(activeRGB).map((keyItem: string) => `${keyItem.toLowerCase()}=${activeRGB[keyItem].band}&${keyItem.toLowerCase()}_range=[${activeRGB[keyItem].range}]&`).join('')
                const buildRasterUrl = `${host}/${activeEndpoint}${keysRasterUrl}?${rgbParams}`
                setSelectedDatasetRasterUrl(buildRasterUrl)

            }

        }

    }, [activeRGB, activeEndpoint, activeDataset, datasets])  // eslint-disable-line react-hooks/exhaustive-deps

    return (
        <SidebarItemWrapper isLoading={isLoading} title={'Search for datasets'}>
            <Box>
                {
                    keys &&
                        <DatasetsForm
                            keys={keys}
                            onSubmitFields={onSubmitFields}
                        />
                }
            </Box>
            <DatasetsColormap />
            <Box className={classes.table}>
                <TableContainer onMouseLeave={() => setHoveredDataset(undefined)}>
                    <Table
                        aria-labelledby="tableTitle"
                        size={"small"} // medium
                        aria-label="enhanced table"
                    >
                        <TableHead>
                            <MuiTableRow>
                                <TableCell className={classes.tableCell} />
                                {keys && (
                                    keys.map((datasetKey: KeyItem, i: number) => (
                                        <TableCell className={classes.tableCell} key={`dataset-key-head-${i}`}>
                                            <Typography color={'primary'} className={classes.tableHeadTypography} variant={'body2'}>
                                                {datasetKey.key}
                                            </Typography>
                                        </TableCell>
                                    ))
                                )}
                            </MuiTableRow>
                        </TableHead>
                        <TableBody>
                            {
                                datasets && datasets.map((dataset: ResponseMetadata200, i: number) => (
                                    <Fragment key={`dataset-${i}`}>
                                        <TableRow
                                            dataset={dataset.keys}
                                            keyVal={`dataset-${i}`}
                                            checked={page * limit + i === activeDataset}
                                            onClick={() => onHandleRow(i)}
                                            onMouseEnter={() => setHoveredDataset(dataset.convex_hull)}
                                        />
                                        <DatasetPreview
                                            activeDataset={activeDataset}
                                            dataset={dataset}
                                            host={host}
                                            i={i}
                                            limit={limit}
                                            page={page}
                                            datasetUrl={selectedDatasetRasterUrl}
                                        />
                                    </Fragment>
                                ))
                            }

                        </TableBody>
                    </Table>
                </TableContainer>
            </Box>
            <TablePagination
                value={limit}
                options={limitOptions}
                onGetValue={(val: number) => setLimit(val)}
                page={page}
                onGetPage={(val: number) => setPage(val)}
                disableNext={limit > (datasets?.length || 0)}
            />
        </SidebarItemWrapper>

    )

}

export default SidebarDatasetsItem
