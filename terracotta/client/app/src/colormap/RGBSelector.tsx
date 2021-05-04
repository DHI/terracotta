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
            activeRGB,
            activeDataset,
            datasets,
            page,
            limit
        },
        actions: {
            setActiveRGB
        }
    } = useContext(AppContext)

    useEffect(() => {

    }, [])

    const datasetPageRange = activeDataset !== undefined && datasets?.[activeDataset - page * limit]?.range
    const minRange = datasetPageRange && datasetPageRange[0]
    const maxRange = datasetPageRange && datasetPageRange[1]
    
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
                            key={`rgb-slider-${color}`}
                            options={datasetBands}
                            max={Number(maxRange)}
                            min={Number(minRange)}
                            sliderValue={[Number(activeRGB[color].range?.[0]), Number(activeRGB[color].range?.[1])]}
                            title={color + ':'}
                            selectValue={activeRGB[color].band}
                            onGetSelectValue={(val) => onGetBandValue(val, color)}
                            onGetSliderValue={(val) => onGetSliderValue(val, color)}
                            step={0.01}
                        />
                    ))
                )
            }
        </Box>
    )

}

export default RGBSelector
