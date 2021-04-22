import React, { FC } from 'react'
import { Box, TableRow, TableCell, Grid, Collapse, Typography } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { ResponseMetadata200 } from "../common/data/getData"
import { CopyToClipboard } from "@dhi-gras/react-components"

const useStyles = makeStyles(() => ({
    imagePreview: {
        height: '90%',
        width: 'auto'
    },
    codeContainer: {
        backgroundColor: '#F8F8F8', 
        overflowX: 'auto', 
        width: 'fit-content', 
        maxWidth: '100%'
    },
    codeContainerText: {
        color: '#86A2B3',
        fontSize: 11
    }
}))

interface Props {
    host: string,
    page: number,
    limit: number,
    i: number,
    activeDataset?: number,
    dataset: ResponseMetadata200,
    keys?: string[],
    datasetUrl?: string
}
const DatasetPreview: FC<Props> = ({
    host,
    page,
    limit,
    i,
    activeDataset,
    dataset,
    datasetUrl
}) => {

    const classes = useStyles()

    return (
        <TableRow>
            <TableCell style={{ padding: 0 }} colSpan={8}>
                <Collapse in={page * limit + i === activeDataset} timeout="auto" unmountOnExit>
                    {
                        datasetUrl && (

                        <Box p={1} className={classes.codeContainer}>
                            <Box width={1} display={'flex'} alignItems={'center'} justifyContent={'space-between'}>
                                <Typography className={classes.codeContainerText}>
                                    <code>
                                        {'Raster url\n'}
                                    </code>
                                </Typography>
                                <Box>
                                    <CopyToClipboard helperText={'Copy to clipboard'} message={datasetUrl}/>
                                </Box>
                            </Box>
                            <code style={{ wordBreak: 'break-all' }}>
                                {datasetUrl}
                            </code>
                        </Box>
                        )
                    }
                    <Grid container>
                        <Grid item xs={6}>
                            <Box p={1} className={classes.codeContainer}>
                            <Typography className={classes.codeContainerText}>
                                <code>
                                    {'Metadata\n'}
                                </code>
                            </Typography>
                                <code style={{ whiteSpace: 'pre' }}>
                                    {'{\n'}
                                    {Object.keys(dataset).reduce(
                                        (acc: string[], keyItem: string, j: number) => 
                                           {
                                                const neededKeys = ['mean', 'range', 'stdev', 'valid_percentage'];
                                                if(neededKeys.includes(keyItem)){
                                                    if(keyItem === 'range'){
                                                        const buildStr = `  ${keyItem}: [${dataset[keyItem]}],\n`
                                                        acc = [...acc, buildStr]
                                                    }else{
                                                        const buildStr = `  ${keyItem}: ${dataset[keyItem]},\n`
                                                        acc = [...acc, buildStr]
                                                    }
                                                
                                                }

                                            return acc
                                           }, []).join('')}
                                    {'}'}
                                </code>
                            </Box>
                        </Grid>
                        <Grid 
                            item 
                            xs={6} 
                            container
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
