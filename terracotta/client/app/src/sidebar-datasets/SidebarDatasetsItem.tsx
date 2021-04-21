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
import AppContext from "./../AppContext"
import { makeStyles } from '@material-ui/core/styles'
import 
    getData, 
    { 
        ResponseDatasets, 
        DatasetItem, 
        ResponseMetadata200, 
        ResponseKeys,
        KeyItem
} from "./../common/data/getData"
import SidebarItemWrapper from "./../sidebar/SidebarItemWrapper"
import TablePagination from "./TablePagination"
import TableRow from "./TableRow"
import DatasetsForm from "./DatasetsForm"
import DatasetPreview from "./DatasetPreview"
import DatasetsColormap from "./../colormap/DatasetsColormap"

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
            datasetBands
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
        const keysReponse = response as ResponseKeys | undefined
        if(keysReponse && keysReponse.hasOwnProperty('keys') && Array.isArray(keysReponse.keys)){
                
            const keysArray = keysReponse.keys.reduce((acc: string[], item: KeyItem) => {
            
                acc = [...acc, item.key]
                return acc

            }, [])
            setKeys(keysArray)
        }
        setIsLoading(false)
    }

    useEffect(() => {

        void getKeys(host)

    }, [host]) // eslint-disable-line react-hooks/exhaustive-deps

    const onHandleRow = (index: number) => {

        const actualIndex = page * limit + index;

        if(activeDataset === actualIndex){
            setActiveDataset(undefined)
            setSelectedDatasetRasterUrl(undefined)
            setActiveSinglebandRange(undefined)
        }else{
            const dataset = datasets?.[index]
            setActiveDataset(actualIndex)
            if(dataset){
                const keysRasterUrl = Object.keys(dataset.keys).map((keyItem: string) => `/${dataset.keys[keyItem]}`).join('') + '/{z}/{x}/{y}.png'
                const buildRasterUrl = `${host}/${activeEndpoint}${keysRasterUrl}?colormap=${colormap.id}&range=${activeSinglebandRange}`
                setSelectedDatasetRasterUrl(buildRasterUrl)
                setActiveSinglebandRange(dataset.range)
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
        void getDatasets(host, page, limit, queryFields)

    }, [host, page, limit, queryFields]) // eslint-disable-line react-hooks/exhaustive-deps

    const onSetRGBRaster = async (dataset: ResponseMetadata200, keys: string) => {
        const noBandKeysURL = `${host}/datasets?` + Object.keys(dataset.keys).map((item: string) => item !== 'band' ? `${item}=${dataset.keys[item]}&` : '' ).join('')
        const response = await getData(noBandKeysURL) as ResponseDatasets
        if(response?.datasets && activeRGB){

            const { datasets } = response
            const activeRGBCopy = activeRGB
            const bands = datasets.map((dataset: DatasetItem) => dataset.band)
            const findRed = bands.find((item: string) => item.includes('red'))
            const findGreen = bands.find((item: string) => item.includes('green'))
            const findBlue = bands.find((item: string) => item.includes('blue'))

            
            console.log(findRed, findGreen, findBlue)
        }
    }


    useEffect(() => {

        if(activeDataset !== undefined && datasets && activeSinglebandRange){
            const dataset = datasets[activeDataset - page * limit]
            const keysRasterUrl = Object.keys(dataset.keys).map((keyItem: string) => `/${dataset.keys[keyItem]}`).join('') + '/{z}/{x}/{y}.png'
            if(activeEndpoint === 'singleband'){

                const buildRasterUrl = `${host}/${activeEndpoint}${keysRasterUrl}?colormap=${colormap.id}&stretch_range=[${activeSinglebandRange}]`
                setSelectedDatasetRasterUrl(buildRasterUrl)

            }

            if(activeEndpoint === 'rgb'){
               void onSetRGBRaster(dataset, keysRasterUrl)
            }
        }

    }, [activeSinglebandRange, colormap, activeDataset, activeEndpoint])

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
                                    keys.map((datasetKey: string, i: number) => (
                                        <TableCell className={classes.tableCell} key={`dataset-key-head-${i}`}>
                                            <Typography color={'primary'} className={classes.tableHeadTypography} variant={'body2'}>
                                                {datasetKey}
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
                                            keys={keys}
                                            limit={limit}
                                            page={page}
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
