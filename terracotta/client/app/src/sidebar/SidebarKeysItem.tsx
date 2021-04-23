import React, { FC, useState, useEffect, useContext } from 'react'
import { Typography, Grid } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import getData, { KeyItem, ResponseKeys } from "./../common/data/getData"
import SidebarItemWrapper from "./SidebarItemWrapper"
import AppContext from "./../AppContext"

interface Props {
    host: string
}

const SidebarKeysItem: FC<Props> = ({
    host
}) => {
    const {
        state: { keys },
        actions: {
            setKeys
        }
    } = useContext(AppContext)

    const [ isLoading, setIsLoading ] = useState<boolean>(true)



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
