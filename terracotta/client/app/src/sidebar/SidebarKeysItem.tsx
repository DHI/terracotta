import React, { FC, useState, useEffect } from 'react'
import { Box, Typography, Grid } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import getData from "./../common/data/getData"

const useStyles = makeStyles(() => ({
    wrapper: {
		margin: 16,
        paddingBottom: 16,
		backgroundColor: '#FFFFFF',
		borderBottom: '1px solid #86A2B3'
	},
}))

interface Props {
    host: string
}

type itemKey = { key: string }

const SidebarKeysItem: FC<Props> = ({
    host
}) => {
    const classes = useStyles()

    const [ keys, setKeys ] = useState<undefined | string[]>(undefined)

    const getKeys = async (host: string) => {
        const response = await getData(`${host}/keys`)
        if(response && response.hasOwnProperty('keys') && Array.isArray(response.keys)){
                
            const keysArray = response.keys.reduce((acc: string[], item: itemKey) => {
            
                acc = [...acc, item.key]
                return acc

            }, [])
            
            setKeys(keysArray)
        }
    }

    useEffect(() => {

        void getKeys(host)

    }, [host])

    return (
        <Box className={classes.wrapper}>
            <Typography variant={'body1'} gutterBottom>
                {'Available keys'}
            </Typography>
          {
              keys && (
                <Grid container spacing={1}>
                    {keys.map((item: string, i: number) => (
                        <Grid xs={6} item key={`key-item-${ i }`}>
                            <Typography variant={'body2'}>
                                { `${i + 1}. ${item}` }
                            </Typography>
                        </Grid>
                    ))}
                </Grid>
              )
          }
        </Box>
    )

}

export default SidebarKeysItem
