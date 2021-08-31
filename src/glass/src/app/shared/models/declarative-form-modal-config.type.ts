import { DeclarativeFormConfig } from '~/app/shared/models/declarative-form-config.type';

export type DeclarativeFormModalConfig = {
  title: string;
  subtitle?: string;
  submitButtonVisible?: boolean; // Defaults to `true`
  submitButtonText?: string; // Defaults to `OK`
  submitButtonResult?: any; // Defaults to form values
  cancelButtonVisible?: boolean; // Defaults to `true`
  cancelButtonText?: string; // Defaults to `Cancel`
  cancelButtonResult?: any; // Defaults to `false`
  cancelButtonClass?: string;
  formConfig: DeclarativeFormConfig;
};
