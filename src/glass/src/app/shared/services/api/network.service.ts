/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */

import { Injectable } from '@angular/core';
import _ from 'lodash';
import { Observable, of } from 'rxjs';

export type Interface = {
  name: string;
  config: {
    bootproto: 'dhcp' | 'static';
    addr?: string;
    netmask?: string;
    gateway?: string;
  };
};

@Injectable({
  providedIn: 'root'
})
export class NetworkService {
  mockInterfaces = [
    {
      name: 'interface-1',
      config: {
        bootproto: 'dhcp'
      }
    },
    {
      name: 'interface-2',
      config: {
        addr: '173.25.46.155',
        bootproto: 'static',
        netmask: '255.255.255.0',
        gateway: '173.25.46.1'
      }
    }
  ] as Interface[];

  public list(): Observable<Interface[]> {
    //return this.http.get<Interface[]>(`${this.url}/`);
    return of(this.mockInterfaces);
  }

  public get(name: string): Observable<Interface> {
    //return this.http.get<Interface>(`${this.url}/${name}`);
    // @ts-ignore
    return of(_.find(this.mockInterfaces, { name })) as Interface;
  }

  public update(networkInterface: Partial<Interface>): Observable<Interface> {
    //return this.http.patch<Interface>(`${this.url}/${networkInterface.name}`, networkInterface);
    // @ts-ignore
    return of(networkInterface) as Interface;
  }
}
