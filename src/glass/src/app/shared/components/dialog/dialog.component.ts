import { Component, Inject, OnInit } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import _ from 'lodash';

import { Icon } from '~/app/shared/enum/icon.enum';
import { GLASS_DIALOG_DATA } from '~/app/shared/services/dialog.service';

export type DialogConfig = {
  type: 'ok' | 'okCancel' | 'yesNo';
  icon?: 'info' | 'warning' | 'danger' | 'question';
  title?: string;
  message: string;
};

@Component({
  selector: 'glass-dialog',
  templateUrl: './dialog.component.html',
  styleUrls: ['./dialog.component.scss']
})
export class DialogComponent implements OnInit {
  public config!: DialogConfig;

  public button1Text!: string;
  public button1Result?: any;
  public button1Class?: string;
  public button1Visible = false;
  public button2Text!: string;
  public button2Result?: any;
  public button2Class?: string;
  public button2Visible = false;
  public icon?: string;

  private icons = Icon;

  constructor(
    public ngbActiveModal: NgbActiveModal,
    @Inject(GLASS_DIALOG_DATA) config: DialogConfig
  ) {
    this.config = config;
  }

  ngOnInit(): void {
    this.button1Class = 'btn-outline-default';
    this.button2Class = 'btn-outline-default';
    switch (this.config.type) {
      case 'ok':
        this.button1Text = TEXT('OK');
        this.button1Result = true;
        this.button1Visible = true;
        this.button1Class = 'btn-submit';
        break;
      case 'okCancel':
        this.button1Text = TEXT('OK');
        this.button1Result = true;
        this.button1Visible = true;
        this.button1Class = 'btn-submit';
        this.button2Text = TEXT('Cancel');
        this.button2Result = false;
        this.button2Visible = true;
        break;
      case 'yesNo':
        this.button1Text = TEXT('Yes');
        this.button1Result = true;
        this.button1Visible = true;
        this.button1Class = 'btn-submit';
        this.button2Text = TEXT('No');
        this.button2Result = false;
        this.button2Visible = true;
        break;
    }
    switch (this.config.icon) {
      case 'info':
        this.icon = this.icons.info;
        break;
      case 'warning':
        this.icon = this.icons.warning;
        this.button1Class = _.replace(this.button1Class, 'btn-submit', 'btn-warning');
        break;
      case 'danger':
        this.icon = this.icons.danger;
        this.button1Class = _.replace(this.button1Class, 'btn-submit', 'btn-danger');
        break;
      case 'question':
        this.icon = this.icons.question;
    }
  }

  onButtonClick(result: any): void {
    this.ngbActiveModal.close(result);
  }
}
