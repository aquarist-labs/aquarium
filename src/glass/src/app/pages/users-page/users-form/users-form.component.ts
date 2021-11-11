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
import { Component, OnInit, ViewChild } from '@angular/core';
import { AbstractControl, AsyncValidatorFn, ValidationErrors } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { Observable, of, timer } from 'rxjs';
import { finalize, map, switchMapTo } from 'rxjs/operators';

import { PageStatus } from '~/app/shared/components/content-page/content-page.component';
import { DeclarativeFormComponent } from '~/app/shared/components/declarative-form/declarative-form.component';
import {
  DeclarativeFormConfig,
  FormFieldConfig
} from '~/app/shared/models/declarative-form-config.type';
import { User, UsersService } from '~/app/shared/services/api/users.service';

@Component({
  selector: 'glass-users-form',
  templateUrl: './users-form.component.html',
  styleUrls: ['./users-form.component.scss']
})
export class UsersFormComponent implements OnInit {
  @ViewChild(DeclarativeFormComponent, { static: false })
  form!: DeclarativeFormComponent;

  @BlockUI()
  blockUI!: NgBlockUI;

  pageStatus: PageStatus = PageStatus.none;
  fields: { [fieldName: string]: FormFieldConfig } = {
    username: {
      type: 'text',
      label: TEXT('Name'),
      name: 'username',
      value: ''
    },
    fullName: {
      type: 'text',
      label: TEXT('Full Name'),
      name: 'full_name',
      value: ''
    },
    password: {
      type: 'password',
      label: TEXT('Password'),
      name: 'password',
      value: ''
    },
    confirmPassword: {
      type: 'password',
      label: TEXT('Confirm password'),
      name: 'passwordconf',
      value: '',
      validators: {
        constraint: {
          constraint: {
            operator: 'eq',
            arg0: { prop: 'password' },
            arg1: { prop: 'passwordconf' }
          },
          errorMessage: TEXT('Password does not match.')
        }
      }
    },
    disabled: {
      type: 'checkbox',
      label: TEXT('Disabled'),
      name: 'disabled',
      value: false,
      hint: TEXT('Temporarily prohibit the user from logging in.')
    }
  };
  // @ts-ignore
  // formConfig won't be used before declaration through the use of ngIf in template.
  formConfig: DeclarativeFormConfig;

  constructor(
    private route: ActivatedRoute,
    private usersService: UsersService,
    private router: Router
  ) {
    this.route.params.subscribe((p: { name?: string }) => {
      if (p.name) {
        this.pageStatus = PageStatus.loading;
        this.usersService.get(p.name!).subscribe(
          (user) => {
            this.pageStatus = PageStatus.ready;
            this.edit(user);
          },
          () => (this.pageStatus = PageStatus.loadingError)
        );
      } else {
        this.pageStatus = PageStatus.ready;
        this.add();
      }
    });
  }

  ngOnInit(): void {}

  add() {
    this.fields.username.validators = { required: true, asyncCustom: this.nameValidator() };
    this.fields.password.validators = { required: true };

    this.setFormConfig(TEXT('Add User'), TEXT('Add'), () =>
      this.userAction('create', TEXT('Please wait, creating user ...'))
    );
  }

  edit(user: User) {
    this.fields.username.value = user.username;
    this.fields.username.readonly = true;
    this.fields.fullName.value = user.full_name;
    this.fields.disabled.value = user.disabled;

    const edit = TEXT('Edit');
    this.setFormConfig(`${edit} ${user.username}`, edit, () =>
      this.userAction('update', TEXT('Please wait, updating user ...'))
    );
  }

  private setFormConfig(title: string, submitButtonText: string, submitFn: () => void) {
    this.formConfig = {
      buttons: [
        {
          type: 'default',
          text: TEXT('Cancel'),
          click: () => this.router.navigate(['dashboard/users'])
        },
        { type: 'submit', text: submitButtonText, click: submitFn }
      ],
      fields: [
        this.fields.username,
        this.fields.fullName,
        this.fields.password,
        this.fields.confirmPassword,
        this.fields.disabled
      ],
      title
    };
  }

  private userAction(actionName: 'create' | 'update', startText: string) {
    this.blockUI.start(startText);
    const action = this.usersService[actionName](this.getUser()) as Observable<any>;
    action
      .pipe(finalize(() => this.blockUI.stop()))
      .subscribe(() => this.router.navigate(['dashboard/users']));
  }

  private getUser(): User {
    return this.form.values as User;
  }

  private nameValidator(): AsyncValidatorFn {
    return (control: AbstractControl): Observable<ValidationErrors | null> =>
      control.pristine || _.isEmpty(control.value)
        ? of(null)
        : timer(200).pipe(
            switchMapTo(this.usersService.exists(control.value)),
            map((resp: boolean) => (resp ? { custom: TEXT('The name is already in use.') } : null))
          );
  }
}
