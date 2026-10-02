import { NavLink } from 'react-router-dom';
import { accountDestination, useAccount } from './account';

export function PublicAccountLinks() {
  const account = useAccount();
  if (account.data)
    return (
      <NavLink to={accountDestination(account.data)}>
        {account.data.email_verified ? 'Minha área' : 'Continuar meu cadastro'}
      </NavLink>
    );
  return (
    <>
      <NavLink to="/entrar">Entrar</NavLink>
      <NavLink to="/criar-conta">Criar conta</NavLink>
    </>
  );
}
