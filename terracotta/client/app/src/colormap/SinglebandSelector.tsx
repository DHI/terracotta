import React, { FC, useState, useContext, useEffect } from 'react'
import { 
    Box, 
    FormControl, 
    Select, 
    MenuItem, 
    InputLabel, 
    Grid 
} from '@material-ui/core'
import AppContext from "./../AppContext"
import Slider from "../common/components/Slider"
import COLORMAPS, { Colormap } from "./colormaps"
import { Legend } from '@dhi-gras/react-components'

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
            activeSinglebandRange
        },
        actions: {
            setColormap,
            setActiveSinglebandRange
        }
    } = useContext(AppContext)

    const [ localRange, setLocalRange ] = useState(activeSinglebandRange)
    const onSetColormap = (colorId: string) => {

        const colormapObj = COLORMAPS.find((item: Colormap) => item.id === colorId)
        if(colormapObj) setColormap(colormapObj)
        
    }

    const onSetRangeValue = (range: number[]) => {
        setActiveSinglebandRange(range)
    }

    useEffect(() => {

        activeSinglebandRange && setLocalRange(activeSinglebandRange)

    }, [activeSinglebandRange])

    return (
        <Grid container alignItems={'center'}>
            <Grid item xs={4}>
                <FormControl fullWidth>
                    <InputLabel>
                        {'Colormap'}
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
                        datasets && activeSinglebandRange !== undefined && activeDataset !== undefined &&(
                        <>
                            <Slider 
                                noNumbers 
                                getValueCommitted={value => Array.isArray(value) && onSetRangeValue(value)} 
                                getValue={(value: number | number[]) => Array.isArray(value) && setLocalRange(value)}
                                defaultValue={activeSinglebandRange} 
                                min={datasets[activeDataset - page * limit]?.range[0] || 0} 
                                max={datasets[activeDataset - page * limit]?.range[1] || 0} 
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
