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

    const minRange = activeDataset !== undefined && datasets?.[activeDataset - page * limit]?.range[0]
    const maxRange = activeDataset !== undefined && datasets?.[activeDataset - page * limit]?.range[1]

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
