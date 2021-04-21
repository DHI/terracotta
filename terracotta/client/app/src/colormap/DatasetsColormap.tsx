import React, { FC, useState, ChangeEvent } from 'react'
import { Box, Typography } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import SidebarItemWrapper from "../sidebar/SidebarItemWrapper"
import Switch from "../common/components/Switch"
import SinglebandSelector from "./SinglebandSelector"
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


interface Props {
    host: string,
    page: number,
    limit: number
}

const DatasetsColormap: FC<Props> = ({
    host,
    page,
    limit
}) => {
    const [ isRGB, setIsRGB ] = useState<boolean>(false)
    const classes = useStyles()

    return (
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
                <Box display={'flex'} alignItems={'center'}>
                    <Typography variant={'body1'} className={classes.rgbText}>
                        Show RGB
                    </Typography>
                    <Switch onChange={(e: ChangeEvent<HTMLInputElement>) => setIsRGB(e.target.checked)}/>
                </Box>
            </Box>
            {
                isRGB ? 
                '' : 
                <SinglebandSelector />
            }
        </Box>
    )

}

export default DatasetsColormap
