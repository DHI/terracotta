import React, { FC, useState, useEffect } from 'react'
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
import { makeStyles } from '@material-ui/core/styles'

import getData, { ResponseDatasets, DatasetItem } from "./../common/data/getData"
import SidebarItemWrapper from "./SidebarItemWrapper"
import TablePagination from "./TablePagination"
import TableRow from "./TableRow"
import DatasetsForm from "./DatasetsForm"

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
        maxHeight: 500
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

interface TableRowCompProps {
    dataset: DatasetItem,
    keyVal: string
}

const limitOptions = [ 15, 25, 50, 100 ]

const SidebarDatasetsItem: FC<Props> = ({
    host
}) => {
    const classes = useStyles()
    const [ datasets, setDatasets ] = useState<undefined | DatasetItem[]>(undefined)
    const [ page, setPage ] = useState<number>(0)
    const [ limit, setLimit ] = useState<number>(15)
    const [ queryFields, setQueryFields ] = useState<string | undefined>(undefined)
    const [ isLoading, setIsLoading ] = useState<boolean>(true)
    const [ keys, setKeys] = useState<string[] | undefined>(undefined)
    const [ activeDataset, setActiveDataset ] = useState<number | undefined>(undefined)

    const getDatasets = async (host: string, pageRef: number, limitRef: number, queryString: string = '') => {
        const response = await getData(`${host}/datasets?limit=${limitRef}&page=${pageRef}${queryString}`)
        const datasetsResponse = response as ResponseDatasets | undefined
        if(datasetsResponse && datasetsResponse.hasOwnProperty('datasets') && Array.isArray(datasetsResponse.datasets)){
           
            setDatasets(datasetsResponse.datasets)
            if(datasetsResponse.datasets[0]){
                const keysCapitalized = Object.keys(datasetsResponse.datasets[0]).map((item: string) => item[0].toUpperCase() + item.substring(1))
                setKeys(keysCapitalized)
            }

        }

        setIsLoading(false)
    }

    const onHandleRow = (index: number) => {

        const actualIndex = page + (page !== 0 ? limit : 0) + index;
        setActiveDataset(actualIndex)

    }

    useEffect(() => {

        setIsLoading(true)
        void getDatasets(host, page, limit, queryFields)

    }, [host, page, limit, queryFields])


    return (
        <SidebarItemWrapper isLoading={isLoading} title={'Search for datasets'}>
            <Box>
                {keys && 
                    <DatasetsForm 
                        keys={keys} 
                        onSubmitFields={(queryString: string) => {
                            setQueryFields(queryString)
                            setPage(0)
                        }}
                        
                    />}
            </Box>
            <Box className={classes.table}>
                <TableContainer>
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
                                datasets && datasets.map((dataset: DatasetItem, i: number) => (
                                    <TableRow 
                                        dataset={dataset} 
                                        keyVal={`dataset-${i}`} key={`dataset-${i}`}
                                        checked={page + (page !== 0 ? limit : 0) + i === activeDataset}
                                        onClick={() => onHandleRow(i)}
                                    />
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
