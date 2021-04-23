import React, { FC, useContext, useEffect } from 'react'
import { 
    Box, 
} from '@material-ui/core'
import AppContext, { activeRGBSelectorRange } from "./../AppContext"
import RGBSlider from "./RGBSlider"

const RGBSelector: FC = () => {
    const {
        state: { 
            datasetBands,
            activeRGB
        },
        actions: {
            setActiveRGB
        }
    } = useContext(AppContext)

    useEffect(() => {

    }, [])

    const onGetBandValue = (val: string, bandKey: string) => {
        setActiveRGB((activeRGB: activeRGBSelectorRange) => activeRGB && {
            ...activeRGB,
            [ bandKey ]: { band: val, range: activeRGB[bandKey].range }
        })
    }

    const onGetSliderValue = (val: number[], sliderKey: string) => {
        setActiveRGB((activeRGB: activeRGBSelectorRange) => activeRGB && {
            ...activeRGB,
            [ sliderKey ]: { range: val, band: activeRGB[sliderKey].band }
        })
    }

    return (
        <Box>
            {
                datasetBands && activeRGB && (
                    Object.keys(activeRGB).map((color: string) => (
                        <RGBSlider 
                            options={datasetBands}
                            max={255}
                            min={0}
                            sliderValue={activeRGB[color].range}
                            title={color + ':'}
                            selectValue={activeRGB[color].band}
                            onGetSelectValue={(val) => onGetBandValue(val, color)}
                            onGetSliderValue={(val) => onGetSliderValue(val, color)}
                        />
                    ))
                )
            }
        </Box>
    )

}

export default RGBSelector
