export type InstallWizardContext = {
  config: Record<string, any>;
  stage: 'unknown' | 'bootstrapping' | 'bootstrapped' | 'deployed';
  stepperVisible: boolean;
};
