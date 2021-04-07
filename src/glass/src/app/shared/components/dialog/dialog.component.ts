import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';

export type DialogConfig = {
  type: 'ok' | 'okCancel' | 'yesNo';
  icon?: 'info' | 'warn' | 'error' | 'danger' | 'question';
  title?: string;
  message: string;
};

@Component({
  selector: 'glass-dialog',
  templateUrl: './dialog.component.html',
  styleUrls: ['./dialog.component.scss']
})
export class DialogComponent implements OnInit {
  config!: DialogConfig;

  button1Text!: string;
  button1Result?: any;
  button1Class?: string;
  button1Visible = false;
  button2Text!: string;
  button2Result?: any;
  button2Visible = false;
  icon?: string;

  constructor(@Inject(MAT_DIALOG_DATA) data: DialogConfig) {
    this.config = data;
  }

  ngOnInit(): void {
    switch (this.config.type) {
      case 'ok':
        this.button1Text = TEXT('OK');
        this.button1Result = true;
        this.button1Visible = true;
        break;
      case 'okCancel':
        this.button1Text = TEXT('OK');
        this.button1Result = true;
        this.button1Visible = true;
        this.button2Text = TEXT('Cancel');
        this.button2Result = false;
        this.button2Visible = true;
        break;
      case 'yesNo':
        this.button1Text = TEXT('Yes');
        this.button1Result = true;
        this.button1Visible = true;
        this.button2Text = TEXT('No');
        this.button2Result = false;
        this.button2Visible = true;
        break;
    }
    switch (this.config.icon) {
      case 'info':
        this.icon = 'mdi:information-outline';
        break;
      case 'warn':
        this.icon = 'mdi:alert-outline';
        this.button1Class = 'glass-color-theme-warn';
        break;
      case 'error':
        this.icon = 'alert-circle-outline';
        this.button1Class = 'glass-color-theme-error';
        break;
      case 'danger':
        this.icon = 'mdi:close-octagon';
        this.button1Class = 'glass-color-theme-danger';
        break;
      case 'question':
        this.icon = 'mdi:help-circle-outline';
    }
  }
}
