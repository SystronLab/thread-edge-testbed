import { writable, type Writable, readable, type Readable } from "svelte/store"

export interface ThreadDevice {
    rloc: string
    ip: string
    platform: string
    ipaddr: string
}

export interface ThreadNetwork {
    channel: string
    panid: string
    networkkey: string
}