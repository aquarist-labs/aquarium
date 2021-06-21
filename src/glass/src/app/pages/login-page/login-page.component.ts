import { Component, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { finalize } from 'rxjs/operators';

import { translate } from '~/app/i18n.helper';
import { DeclarativeFormComponent } from '~/app/shared/components/declarative-form/declarative-form.component';
import { DeclarativeFormConfig } from '~/app/shared/models/declarative-form-config.type';
import { AuthService } from '~/app/shared/services/api/auth.service';

@Component({
  selector: 'glass-login-page',
  templateUrl: './login-page.component.html',
  styleUrls: ['./login-page.component.scss']
})
export class LoginPageComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  @ViewChild(DeclarativeFormComponent, { static: true })
  form!: DeclarativeFormComponent;

  public config: DeclarativeFormConfig = {
    id: 'loginPage',
    fields: [
      {
        name: 'username',
        type: 'text',
        label: TEXT('Username'),
        value: '',
        validators: {
          required: true
        }
      },
      {
        name: 'password',
        type: 'password',
        label: TEXT('Password'),
        value: '',
        validators: {
          required: true
        }
      }
    ]
  };

  constructor(private authService: AuthService, private router: Router) {}

  ngOnInit(): void {
    this.blockUI.resetGlobal();
  }

  onLogin(): void {
    this.blockUI.start(translate(TEXT('Please wait ...')));
    const values = this.form.values;
    this.authService
      .login(values.username, values.password)
      .pipe(finalize(() => this.blockUI.stop()))
      .subscribe(() => {
        this.router.navigate(['/dashboard']);
      });
  }
}
