import React, { FC, useState, useContext, useEffect } from 'react'
import { 
    Box, 
    Typography, 
    FormControl, 
    Select, 
    MenuItem, 
    InputLabel, 
    Grid 
} from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import AppContext from "./../AppContext"
import COLORMAPS, { Colormap } from "./colormaps"
import { Legend } from '@dhi-gras/react-components'
import Slider from "../common/components/Slider"

const useStyles = makeStyles(() => ({
    headingText: {
        fontSize: 12,
        fontWeight: 600
    }
}))

// reds
interface Props {

}

const SinglebandSelector: FC<Props> = () => {
    const {
        state: { 
            colormap,
            activeDataset,
            page,
            limit,
            datasets,
            activeRange
        },
        actions: {
            setColormap,
            setActiveRange
        }
    } = useContext(AppContext)

    const [ localRange, setLocalRange ] = useState(activeRange)
    const onSetColormap = (colorId: string) => {

        const colormapObj = COLORMAPS.find((item: Colormap) => item.id === colorId)
        if(colormapObj) setColormap(colormapObj)
        
    }

    const onSetRangeValue = (range: number[]) => {
        setActiveRange(range)
    }

    useEffect(() => {

        activeRange && setLocalRange(activeRange)

    }, [activeRange])

    return (
        <Grid container alignItems={'center'}>
            <Grid item xs={4}>
                <FormControl fullWidth>
                    <InputLabel>
                    {'Choose a colormap'}
                    </InputLabel>
                    <Select
                        id="demo-simple-select-outlined"
                        value={colormap.id}
                        onChange={(e) => onSetColormap(String(e.target.value))}
                        fullWidth
                    >
                        {
                            COLORMAPS.map((option: Colormap, i: number) => (
                                <MenuItem key={`limit-${option.id}`} value={option.id}>{option.displayName}</MenuItem>
                            ))
                        }
                    </Select>
                </FormControl>
            </Grid>
            <Grid item xs={8}>
                <Box mx={4}>
                    {
                        datasets && activeDataset !== undefined && activeRange !== undefined && (
                        <>
                            <Slider 
                                noNumbers 
                                getValueCommitted={value => Array.isArray(value) && onSetRangeValue(value)} 
                                getValue={(value: any) => setLocalRange(value)}
                                defaultValue={activeRange} 
                                min={datasets[activeDataset - page * limit].range[0]} 
                                max={datasets[activeDataset - page * limit].range[1]} 
                                step={0.01} 
                                title={'Contrast '}
                            />
                            <Legend 
                                src={colormap.img_url} 
                                range={localRange}
                                length={2}
                            />
                        </>
                        )
                    }
                </Box>
            </Grid>
        </Grid>
    )

}

export default SinglebandSelector
