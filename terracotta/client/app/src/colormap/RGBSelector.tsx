import React, { FC, useState, useContext, useEffect } from 'react'
import { 
    Box, 
} from '@material-ui/core'
import AppContext from "./../AppContext"
import RGBSlider from "./RGBSlider"

// reds
interface Props {

}

const RGBSelector: FC<Props> = () => {
    const {
        state: { 
            datasetBands,
            activeRGB
        },
        actions: {
            setColormap,
            setActiveSinglebandRange
        }
    } = useContext(AppContext)

    useEffect(() => {

    }, [])

    return (
        <Box>
            {
                activeRGB && datasetBands && (
                    Object.keys(activeRGB).map((color: string) => (
                        <RGBSlider 
                            options={datasetBands}
                            max={255}
                            min={0}
                            sliderValue={activeRGB[color].range}
                            title={color}
                            selectValue={activeRGB[color].band}
                            onGetSelectValue={(val) => console.log(val)}
                            onGetSliderValue={(val) => console.log(val)}
                        />
                    ))
                )
            }
        </Box>
    )

}

export default RGBSelector
