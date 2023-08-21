import React, { FC, ReactNode } from 'react'
import { Box, Typography, CircularProgress } from '@mui/material'

const styles = {
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
}

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

    return (
        <Box sx={styles.wrapper}>
            <Box display={'flex'} alignItems={'center'} mb={1}>
                <Typography variant={'body1'}>
                    {title}
                </Typography>
                {
                    isLoading && <CircularProgress color={'primary'} sx={styles.spinner}/>
                }
            </Box>
            {children}
        </Box>
    )

}

export default SidebarItemWrapper
