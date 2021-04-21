import React, { FC } from 'react'
import { Box, TableRow, TableCell, Grid, Collapse } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { ResponseMetadata200 } from "../common/data/getData"

const useStyles = makeStyles(() => ({
    imagePreview: {
        height: '90%',
        width: 'auto'
    }
}))

interface Props {
    host: string,
    page: number,
    limit: number,
    i: number,
    activeDataset?: number,
    dataset: ResponseMetadata200,
    keys?: string[]
}
const DatasetPreview: FC<Props> = ({
    host,
    page,
    limit,
    i,
    activeDataset,
    dataset,
}) => {

    const classes = useStyles()

    return (
        <TableRow>
            <TableCell style={{ padding: 0 }} colSpan={8}>
                <Collapse in={page * limit + i === activeDataset} timeout="auto" unmountOnExit>
                    <Grid container spacing={1}>
                        <Grid item xs={6}>
                            <Box p={1} style={{ backgroundColor: '#F8F8F8', overflowX: 'auto', width: 'fit-content', maxWidth: '100%' }}>
                                <code style={{ whiteSpace: 'pre' }}>
                                    {'{\n'}
                                    {Object.keys(dataset).reduce(
                                        (acc: string[], keyItem: string, j: number) => 
                                           {
                                                const neededKeys = ['mean', 'range', 'stdev', 'valid_percentage'];
                                                if(neededKeys.includes(keyItem)){
                                                    if(keyItem === 'range'){
                                                        const buildStr = `  ${keyItem}: [${(dataset as any)[keyItem]}],\n`
                                                        acc = [...acc, buildStr]
                                                    }else{
                                                        const buildStr = `  ${keyItem}: ${(dataset as any)[keyItem]},\n`
                                                        acc = [...acc, buildStr]
                                                    }
                                                
                                                }

                                            // (`\t${keyItem.toLowerCase()}: ${dataset[keyItem.toLowerCase()]}${j !== keys.length - 1 ? "," : ''}\n`)
                                            return acc
                                           }, []).join('')}
                                    {'}'}
                                </code>
                            </Box>
                        </Grid>
                        <Grid 
                            item 
                            container 
                            xs={6} 
                            justify={'center'}
                            alignItems={'center'}
                        >
                            <img
                                src={`${host}/singleband/${Object.keys(dataset.keys).map((datasetKey: string) => `${dataset.keys[datasetKey]}/`).join('')}preview.png?tile_size=[128,128]`} 
                                alt={'TC-preview'}
                                className={classes.imagePreview}
                                loading={'eager'}
                            />
                        </Grid>
                    </Grid>
                </Collapse>
            </TableCell>
        </TableRow>
    )

}

export default DatasetPreview
