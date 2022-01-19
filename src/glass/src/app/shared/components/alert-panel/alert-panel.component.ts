/* eslint-disable no-underscore-dangle */
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
import { BooleanInput, coerceBooleanProperty } from '@angular/cdk/coercion';
import { Component, Input, OnInit } from '@angular/core';

import { Icon } from '~/app/shared/enum/icon.enum';

@Component({
  selector: 'glass-alert-panel',
  templateUrl: './alert-panel.component.html',
  styleUrls: ['./alert-panel.component.scss']
})
export class AlertPanelComponent implements OnInit {
  @Input()
  type: 'success' | 'info' | 'warning' | 'danger' | 'hint' = 'danger';

  public bsType = 'danger';
  public icons = Icon;
  public _noColor = false;

  @Input()
  get noColor(): boolean {
    return this._noColor;
  }
  set noColor(value: BooleanInput) {
    this._noColor = coerceBooleanProperty(value);
  }

  ngOnInit(): void {
    switch (this.type) {
      case 'success':
        this.bsType = 'success';
        break;
      case 'info':
        this.bsType = 'info';
        break;
      case 'warning':
        this.bsType = 'warning';
        break;
      case 'danger':
        this.bsType = 'danger';
        break;
      case 'hint':
        this.bsType = 'info';
        break;
    }
  }
}
