import React, { FC, useContext } from 'react'
import { Box, Typography, Collapse, FormControl, Select, MenuItem } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import SinglebandSelector from "./SinglebandSelector"
import RGBSelector from "./RGBSelector"
import AppContext from "./../AppContext"
import endpoints, { Endpoint } from "./endpoints"

const useStyles = makeStyles(() => ({
    wrapper: {
		margin: 16,
        paddingBottom: 16,
		backgroundColor: '#FFFFFF',
		borderBottom: '1px solid #86A2B3'
	},
    rgbText: {
        fontSize: 12,
        marginRight: 6
    }
}))

const DatasetsColormap: FC = () => {

    const {
        state: { 
            activeDataset,
            activeEndpoint
        },
        actions: {
            setActiveEndpoint
        }
    } = useContext(AppContext)

    const classes = useStyles()

    return (
            <Collapse in={activeDataset !== undefined} timeout="auto" unmountOnExit>
                <Box className={classes.wrapper}>
                    <Box 
                        display={'flex'} 
                        alignItems={'center'} 
                        mb={1}
                        justifyContent={'space-between'}
                    >
                        <Typography variant={'body1'}>
                            {'Customize layer'}
                        </Typography>
                        <Box display={'flex'} alignItems={'center'} style={{ minWidth: 100 }}>
                            <FormControl fullWidth>
                                <Select
                                    id="demo-simple-select-outlined"
                                    value={activeEndpoint}
                                    onChange={(e) => setActiveEndpoint(String(e.target.value))}
                                    fullWidth
                                >
                                    {
                                        endpoints.map((option: Endpoint) => (
                                            <MenuItem key={`endpoint-${option.id}`} value={option.id}>{option.id}</MenuItem>
                                        ))
                                    }
                                </Select>
                            </FormControl>
                        </Box>
                    </Box>
                        {
                            activeEndpoint === 'singleband' &&  <SinglebandSelector />
                        }
                        {
                            activeEndpoint === 'rgb' &&  <RGBSelector />
                        }
                </Box>
            </Collapse>
    )

}

export default DatasetsColormap
