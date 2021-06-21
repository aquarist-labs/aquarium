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
/* eslint-disable @typescript-eslint/naming-convention */
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type User = {
  username: string;
  password: string;
  full_name: string;
  disabled: boolean;
};

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private url = 'api/user';
  constructor(private http: HttpClient) {}

  public list(): Observable<User[]> {
    return this.http.get<User[]>(`${this.url}/`);
  }

  public create(user: User): Observable<void> {
    return this.http.post<void>(`${this.url}/create`, user);
  }

  public delete(username: string): Observable<void> {
    return this.http.delete<void>(`${this.url}/${username}`);
  }

  public update(username: string, user: Partial<User>): Observable<User> {
    return this.http.patch<User>(`${this.url}/${username}`, user);
  }
}
