import React, { FC, ReactNode } from 'react'
import { Box, Typography, CircularProgress } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles(() => ({
    wrapper: {
		margin: 16,
        paddingBottom: 16,
		backgroundColor: '#FFFFFF',
		borderBottom: '1px solid #86A2B3'
	},
    spinner: {
        width: "16px !important",
        height: "16px !important",
        marginLeft: 6
    }
}))

interface Props {
    isLoading?: boolean,
    title: string,
    children: ReactNode
}
const SidebarItemWrapper: FC<Props> = ({
    isLoading,
    title,
    children
}) => {

    const classes = useStyles()

    return (
        <Box className={classes.wrapper}>
            <Box display={'flex'} alignItems={'center'} mb={1}>
                <Typography variant={'body1'}>
                    {title}
                </Typography>
                {
                    isLoading && <CircularProgress color={'primary'} className={classes.spinner}/>
                }
            </Box>
            {children}
        </Box>
    )

}

export default SidebarItemWrapper
