import React, { FC, useState, useEffect } from 'react'
import { Typography, Grid } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import getData, { KeyItem, ResponseKeys } from "./../common/data/getData"
import SidebarItemWrapper from "./SidebarItemWrapper"
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

const SidebarKeysItem: FC<Props> = ({
    host
}) => {

    const [ keys, setKeys ] = useState<undefined | string[]>(undefined)
    const [ isLoading, setIsLoading ] = useState<boolean>(true)
    const getKeys = async (host: string) => {
        const response = await getData(`${host}/keys`)
        const keysReponse = response as ResponseKeys | undefined
        if(keysReponse && keysReponse.hasOwnProperty('keys') && Array.isArray(keysReponse.keys)){
                
            const keysArray = keysReponse.keys.reduce((acc: string[], item: KeyItem) => {
            
                acc = [...acc, item.key]
                return acc

            }, [])
            
            setKeys(keysArray)
        }
        setIsLoading(false)
    }

    useEffect(() => {

        void getKeys(host)

    }, [host])

    return (
        <SidebarItemWrapper isLoading={isLoading} title={'Available keys'}>
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
        </SidebarItemWrapper>
       
    )

}

export default SidebarKeysItem
