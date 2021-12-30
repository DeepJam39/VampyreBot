import discord
from discord.ext import commands
from sqlalchemy.orm import sessionmaker, joinedload
from cogs.orm import models
from reactionmenu import ButtonsMenu, ComponentsButton
import cogs.orm.database_connection as db
db.load_db()
Session = sessionmaker(bind=db.engine)
admin_role = 'Bot Admin'

def is_admin(member):
    return admin_role in [role.name for role in member.roles]
            

def apply_delta(character_name, amount, trait_name, min_value=0, max_value=None):
    session = Session()
    character = session.query(models.Character).options(joinedload(models.Character.traits).joinedload(
        models.CharacterTrait.trait)).filter(models.Character.name.ilike(f'%{character_name}%')).first()
    if character is None:
        session.close()
        return f"Personaje **{character_name}** no encontrado."
    trait = None
    for t in character.traits:
        if t.trait.name == trait_name:
            trait = t
            break
    if trait is None:
        session.close()
        return f"El personaje **{character.name}** no posee el rasgo **{trait_name}**."
    
    new_value = trait.value + amount
    
    if min_value is not None and type(min_value)==str:
        for t in character.traits:
            if t.trait.name == min_value:
                min_value = t.value
                break
                
    if max_value is not None and type(max_value)==str:
        for t in character.traits:
            if t.trait.name == max_value:
                max_value = t.value
                break
                
    limit_flag = ''
    if new_value <= min_value:
        new_value = min_value
        limit_flag = f' *Valor mínimo.*'
    elif max_value is not None and new_value >= max_value:
        new_value = max_value
        limit_flag = f' *Valor máximo.*'
    
    trait.value = new_value
    confirm_text = f"El rasgo **{trait.trait.name}** de **{character.name}** ahora vale: **{new_value}**.{limit_flag}"
    
    session.commit()
    session.close()
    return confirm_text
    
blood_delta = lambda character_name, amount: apply_delta(character_name, 
                                                         amount, 'Reserva de sangre (actual)', 
                                                         min_value=0, 
                                                         max_value='Reserva de sangre (máxima)')

wp_delta = lambda character_name, amount: apply_delta(character_name, 
                                                      amount, 'Fuerza de Voluntad (temporal)', 
                                                      min_value=0, 
                                                      max_value='Fuerza de Voluntad (permanente)')

pwp_delta = lambda character_name, amount: apply_delta(character_name, 
                                                      amount, 'Fuerza de Voluntad (permanente)', 
                                                      min_value='Fuerza de Voluntad (temporal)', 
                                                      max_value=None)

hp_delta = lambda character_name, amount: apply_delta(character_name, 
                                                      amount, 'Salud (actual)', 
                                                      min_value=0, 
                                                      max_value='Salud (máxima)')

agg_delta = lambda character_name, amount: apply_delta(character_name, 
                                                       amount, 'Daño agravado')

leth_delta = lambda character_name, amount: apply_delta(character_name, 
                                                       amount, 'Daño letal')

async def apply_time_effects(day, channel):
    updated = 0
    
    try:
        session = Session()
        characters = session.query(models.Character).all()
        ghoul_loss = (day % 30 == 0)

        mblood = session.query(models.Trait).filter(models.Trait.name == 'Reserva de sangre (máxima)').first()
        blood = session.query(models.Trait).filter(models.Trait.name == 'Reserva de sangre (actual)').first()
        pwp = session.query(models.Trait).filter(models.Trait.name == 'Fuerza de Voluntad (permanente)').first()
        wp = session.query(models.Trait).filter(models.Trait.name == 'Fuerza de Voluntad (temporal)').first()
        mhp = session.query(models.Trait).filter(models.Trait.name == 'Salud (máxima)').first()
        hp = session.query(models.Trait).filter(models.Trait.name == 'Salud (actual)').first()
        agg = session.query(models.Trait).filter(models.Trait.name == 'Daño agravado').first()
        leth = session.query(models.Trait).filter(models.Trait.name == 'Daño letal').first()

        for character in characters:
            if character.activity == 0:
                continue            
            # willpower gain
            c_pwp = session.query(models.CharacterTrait).filter(
                models.CharacterTrait.character_id==character.id, models.CharacterTrait.trait_id==pwp.id).first()
            c_wp = session.query(models.CharacterTrait).filter(
                models.CharacterTrait.character_id==character.id, models.CharacterTrait.trait_id==wp.id).first()
            if c_wp is not None and c_pwp is not None:
                if c_wp.value < c_pwp.value:
                    c_wp.value += 1

            # Vampires    
            if type(character) == models.Vampire:
                # agg loss
                c_agg = session.query(models.CharacterTrait).filter(
                    models.CharacterTrait.character_id==character.id, models.CharacterTrait.trait_id==agg.id).first()

                c_agg_value = 0
                if c_agg is not None and c_agg.value > 0:
                    c_agg.value -= 1
                    c_agg_value = c_agg.value

                # leth loss
                c_leth = session.query(models.CharacterTrait).filter(
                    models.CharacterTrait.character_id==character.id, models.CharacterTrait.trait_id==leth.id).first()
                if c_leth is not None:
                    c_leth.value = 0

                # life gain
                c_mhp = session.query(models.CharacterTrait).filter(
                    models.CharacterTrait.character_id==character.id, models.CharacterTrait.trait_id==mhp.id).first()
                c_hp = session.query(models.CharacterTrait).filter(
                    models.CharacterTrait.character_id==character.id, models.CharacterTrait.trait_id==hp.id).first()

                if c_hp is not None and c_mhp is not None:
                    c_hp.value = c_mhp.value - 3*c_agg_value

                # blood loss
                c_blood = session.query(models.CharacterTrait).filter(
                    models.CharacterTrait.character_id==character.id, models.CharacterTrait.trait_id==blood.id).first() 

                if c_blood is not None and c_blood.value > 0:
                    c_blood.value -= 1

            # Mortals and Ghouls
            else:
                # leth loss
                c_leth = session.query(models.CharacterTrait).filter(
                    models.CharacterTrait.character_id==character.id, models.CharacterTrait.trait_id==leth.id).first()
                c_leth_value = 0

                if c_leth is not None and c_leth.value > 0:
                    c_leth.value -= 1
                    c_leth_value = c_leth.value

                # life gain
                c_mhp = session.query(models.CharacterTrait).filter(
                    models.CharacterTrait.character_id==character.id, models.CharacterTrait.trait_id==mhp.id).first()
                c_hp = session.query(models.CharacterTrait).filter(
                    models.CharacterTrait.character_id==character.id, models.CharacterTrait.trait_id==hp.id).first()

                if c_hp is not None and c_mhp is not None:
                    c_hp.value = c_mhp.value - 2*c_leth_value

                # Ghouls blood loss
                if ghoul_loss and type(character) == models.Ghoul:
                    c_blood = session.query(models.CharacterTrait).filter(
                        models.CharacterTrait.character_id==character.id, models.CharacterTrait.trait_id==blood.id).first() 

                    if c_blood is not None and c_blood.value > 0:
                        c_blood.value -= 1
            updated += 1
    except Exception as e:
        session.rollback()
        await channel.send(str(e))
    else:
        session.commit()
        await channel.send(
            f"Una nueva noche comienza. {updated} personaje{'s' if updated!=0 else ''} actualizado{'s' if updated!=0 else ''}."
        )
    finally:
        session.close()
        
def read_from_table(table, session, first = False, filters = None):
    query = session.query(table).options(joinedload('*'))
    if filters is not None:
        query = query.filter(*filters)
    rows = query.first() if first else query.all()
    return rows

async def table_refresh_buttons(menu):
    menu.remove_all_buttons()
    page = menu._pc.current_page
    items = {}
    try:
        if menu.model_class == models.Generation:
            items = {int(i.split(' - ')[0]):i.split(' - ')[1].split(' ')[0] for i in page.description.split('\n')}
        else:
            items = {int(i.split(' - ')[0]):i.split(' - ')[1] for i in page.description.split('\n')}

    except IndexError:
        pass

    async def open_item_menu(menu, item_name):
        item_menu = ButtonsMenu(menu._ctx, menu_type=ButtonsMenu.TypeEmbed, show_page_director=False, timeout=300)
        item_menu.model_class = menu.model_class
        session = Session()
        await init_menu_from_item(item_menu, session, filters = [item_menu.model_class.name == item_name])
        session.close()
        await item_menu.start()
        await menu.stop(delete_menu_message=True)

    buttons = []

    if is_admin(menu.owner):
        call_followup = ComponentsButton.Followup()
        call_followup.set_caller_details(add_item, menu)
        buttons.append(ComponentsButton(style=ComponentsButton.style.success, label='Añadir',
                        custom_id=ComponentsButton.ID_CALLER, followup=call_followup))
    for i in list(items):
        call_followup = ComponentsButton.Followup()
        call_followup.set_caller_details(open_item_menu, menu, items[i])
        buttons.append(ComponentsButton(style=ComponentsButton.style.grey, label=f'{i}',
                                         custom_id=ComponentsButton.ID_CALLER, 
                                         followup=call_followup))

    n_pages = len(menu._ButtonsMenu__pages)
    if n_pages > 1:
        buttons.append(ComponentsButton(style=ComponentsButton.style.primary, label='Página Anterior',
                                           custom_id=ComponentsButton.ID_PREVIOUS_PAGE))
        buttons.append(ComponentsButton(style=ComponentsButton.style.primary, label='Página Siguiente',
                                           custom_id=ComponentsButton.ID_NEXT_PAGE))
        if n_pages > 3:
            buttons.append(ComponentsButton(style=ComponentsButton.style.primary, label='Seleccionar Página',
                                               custom_id=ComponentsButton.ID_GO_TO_PAGE))

    buttons.append(ComponentsButton(style=ComponentsButton.style.primary, label='Cerrar',
                                          custom_id=ComponentsButton.ID_END_SESSION))  
    for button in buttons:
        menu._bypass_primed = True
        menu.add_button(button)
    await menu.refresh_menu_buttons()


async def add_trait_value(menu):
    menu.disable_all_buttons()
    await menu.refresh_menu_buttons()
    embed = discord.Embed(title=f"Nuevo rasgo", colour=discord.Colour.blue(),
                          description=f"Introduzca el nombre del rasgo. Por ejemplo:\n\n\
                          `Atletismo`\n\n\
                          O escriba \"Ninguno\" para regresar:\n\n\
                          `Ninguno`")
    bot_message = await menu._ctx.send(embed = embed)

    success = False

    while not success: 
        try:            
            user_response = await menu._bot.wait_for('message', check=lambda m: m.channel.id == menu.message.channel.id 
                                               and m.author.id == menu._ctx.author.id, timeout=menu.timeout)
            value = (user_response.content)                
            if menu.delete_interactions:
                await user_response.delete()

            if value == 'Ninguno':
                value = None

            else:
                session = Session()
                target = session.query(models.Trait).filter(models.Trait.name.ilike(f'%{value}%')).first()
                session.close()
                if target is None:
                    raise ValueError
                else:
                    value = target.name

        except TimeoutError:
            continue

        except ValueError:
            await menu._ctx.send("Valor incorrecto, inténtelo de nuevo.", delete_after=10)
        else:
            success = True    
            await bot_message.delete()    
            if value is None:
                menu.enable_all_buttons()
                await menu.refresh_menu_buttons()
                continue

            await edit_trait_value(menu, value)


async def edit_trait_value(menu, trait_name):
    menu.disable_all_buttons()
    await menu.refresh_menu_buttons()
    embed = discord.Embed(title=f"{trait_name}", colour=discord.Colour.blue(),
                          description=f"Introduzca un nuevo valor de {trait_name}, seguido \
                          opcionalmente de especialidades o especificaciones. Por ejemplo:\n\n\
                          `5 Saltar muros`\n\n\
                          O escriba \"Ninguno\" para eliminar el rasgo del personaje:\n\n\
                          `Ninguno`")
    bot_message = await menu._ctx.send(embed = embed)

    success = False

    while not success:    
        try:            
            user_response = await menu._bot.wait_for('message', check=lambda m: m.channel.id == menu.message.channel.id 
                                               and m.author.id == menu._ctx.author.id, timeout=menu.timeout)
            value = (user_response.content)                
            if menu.delete_interactions:
                await user_response.delete()

            if value == 'Ninguno':
                value = None
            else:
                value = value.strip()
                sep = value.find(' ')
                if sep > -1:
                    value, specs = int(value[:sep]), value[sep+1:]
                else:
                    value, specs = int(value), None

        except TimeoutError:
            continue
        except ValueError:
            await menu._ctx.send("Valor incorrecto, inténtelo de nuevo.", delete_after=10)
        else:
            success = True
            session = Session()
            trait_id = session.query(models.Trait).filter(models.Trait.name.ilike(f'%{trait_name}%')).first().id
            trait = session.query(models.CharacterTrait).filter(models.CharacterTrait.character_id == menu.item.id,
                                                               models.CharacterTrait.trait_id == trait_id).first()
            if value is None:
                if trait is not None:
                    session.delete(trait)
            elif trait is None:
                trait = models.CharacterTrait(
                    character_id = menu.item.id, trait_id = trait_id, value = value, specs = specs)
                session.add(trait)
            else:
                trait.value = value
                trait.specs = specs

            session.commit()
            menu.item = session.query(models.Character).options(
                joinedload(models.Character.traits).joinedload(models.CharacterTrait.trait)).filter(
                models.Character.id == menu.item.id).first()            
            session.close()

            #for t in menu.item.traits:
            #    print(f"{t.trait.name} {t.value}")

            await bot_message.delete()            

            traits_menu = ButtonsMenu(menu._ctx, menu_type=ButtonsMenu.TypeEmbedDynamic, rows_requested = 10,
                  custom_embed=discord.Embed(title=f'Rasgos de {menu.item.name}', colour=discord.Colour.blue()),
                  style="Página $ de &")
            traits_menu.model_class = models.CharacterTrait
            traits_menu.item = menu.item
            await init_menu_from_table(traits_menu, rows = menu.item.traits)
            await traits_menu.start()
            traits_menu.set_relay(traits_menu_listener)

            page_index = menu._pc.index            
            traits_menu._pc.index = page_index
            await traits_menu.message.edit(embed=traits_menu._pc.current_page) 

            await traits_refresh_buttons(traits_menu)
            await menu.stop(delete_menu_message=True)

async def traits_refresh_buttons(menu):
    menu.remove_all_buttons()
    page = menu._pc.current_page
    items = {}
    
    if not page.description == "No se encontraron elementos.":
        items = {int(i[:i.find(' - ')]):i[i.find(' - ')+3:i.rfind(': ')] for i in page.description.split('\n')}

    buttons = []

    if is_admin(menu.owner):
        call_followup = ComponentsButton.Followup()
        call_followup.set_caller_details(add_trait_value, menu)
        buttons.append(ComponentsButton(style=ComponentsButton.style.success, label='Añadir',
                        custom_id=ComponentsButton.ID_CALLER, followup=call_followup))
    for i in list(items):
        call_followup = ComponentsButton.Followup()
        call_followup.set_caller_details(edit_trait_value, menu, items[i])
        buttons.append(ComponentsButton(style=ComponentsButton.style.grey, label=f'{i}',
                                         custom_id=ComponentsButton.ID_CALLER, 
                                         followup=call_followup))

    n_pages = len(menu._ButtonsMenu__pages)
    if n_pages > 1:
        buttons.append(ComponentsButton(style=ComponentsButton.style.primary, label='Página Anterior',
                                           custom_id=ComponentsButton.ID_PREVIOUS_PAGE))
        buttons.append(ComponentsButton(style=ComponentsButton.style.primary, label='Página Siguiente',
                                           custom_id=ComponentsButton.ID_NEXT_PAGE))
        if n_pages > 3:
            buttons.append(ComponentsButton(style=ComponentsButton.style.primary, label='Seleccionar Página',
                                               custom_id=ComponentsButton.ID_GO_TO_PAGE))

    buttons.append(ComponentsButton(style=ComponentsButton.style.primary, label='Cerrar',
                                          custom_id=ComponentsButton.ID_END_SESSION))  
    for button in buttons:
        menu._bypass_primed = True
        menu.add_button(button)
    await menu.refresh_menu_buttons()

async def traits_menu_listener(payload):
    button = payload.button
    menu = button.menu
    #member = payload.member
    #channel = menu.message.channel
    if button.custom_id in (ComponentsButton.ID_PREVIOUS_PAGE, 
                            ComponentsButton.ID_NEXT_PAGE, ComponentsButton.ID_GO_TO_PAGE):
        await traits_refresh_buttons(menu)

async def table_menu_listener(payload):
    button = payload.button
    menu = button.menu
    #member = payload.member
    #channel = menu.message.channel
    if button.custom_id in (ComponentsButton.ID_PREVIOUS_PAGE, 
                            ComponentsButton.ID_NEXT_PAGE, ComponentsButton.ID_GO_TO_PAGE):
        await table_refresh_buttons(menu)

async def item_menu_listener(payload):
    button = payload.button
    menu = button.menu
    member = payload.member
    channel = menu.message.channel

    if button.custom_id in (ComponentsButton.ID_PREVIOUS_PAGE, 
                            ComponentsButton.ID_NEXT_PAGE, ComponentsButton.ID_GO_TO_PAGE):
        await table_refresh_buttons(menu)

async def add_item(menu):
    item = (menu.model_class)()
    item_menu = ButtonsMenu(menu._ctx, menu_type=ButtonsMenu.TypeEmbed, show_page_director=False, timeout=300)
    item_menu.model_class = menu.model_class
    await init_menu_from_item(item_menu, item = item)
    await item_menu.start()    
    await menu.stop(delete_menu_message=True)

async def save_edition_yes(menu, edit_variables, data_pages, data_buttons):
    menu.show_page_director = False
    menu.edited = False
    session = Session()
    row = read_from_table(menu.model_class, session, True, filters = [menu.model_class.id == menu.item.id])
    if row is None:
        row = menu.item
        if menu.model_class is models.Character:
            if menu.item.race_id is not None:
                race_name = session.query(models.Race).filter(models.Race.id == menu.item.race_id).first().name
                menu.model_class = {'Vampiro':models.Vampire, 'Ghoul':models.Ghoul}.get(race_name, models.Character)

                row = menu.model_class(id=menu.item.id)
            for variable in edit_variables:
                setattr(row, variable['name'], getattr(menu.item, variable['name'], None))
        session.add(row)
    else:
        for variable in edit_variables:
            setattr(row, variable['name'], getattr(menu.item, variable['name'], None))
    session.commit()
    menu.item = read_from_table(menu.model_class, session, True, filters = [menu.model_class.name == menu.item.name])
    data_pages.clear()
    data_pages.append(discord.Embed(title=row.short_str(), description=str(row), colour=discord.Colour.blue()))
    session.close()
    await menu.update(data_pages, data_buttons)

async def save_edition_no(menu, edit_pages, edit_buttons):
    menu.show_page_director = True
    await menu.update(edit_pages, edit_buttons)

async def save_edition(menu, edit_variables, data_pages, data_buttons, edit_pages, edit_buttons):
    if menu.edited:
        menu.show_page_director = False
        confirm_page = [discord.Embed(title="Guardar cambios", colour=discord.Colour.blue(),
                                  description="¿Está seguro de que desea guardar los cambios realizados?")]
        confirm_buttons = []

        save_followup_yes = ComponentsButton.Followup()
        save_followup_yes.set_caller_details(save_edition_yes, menu, edit_variables, 
                                               data_pages, data_buttons)
        confirm_buttons.append(ComponentsButton(style=ComponentsButton.style.green, label='Guardar cambios',
                                             custom_id=ComponentsButton.ID_CALLER,
                                             followup=save_followup_yes))

        save_followup_no = ComponentsButton.Followup()
        save_followup_no.set_caller_details(save_edition_no, menu, edit_pages, edit_buttons)
        confirm_buttons.append(ComponentsButton(style=ComponentsButton.style.primary, label='Seguir editando',
                                             custom_id=ComponentsButton.ID_CALLER,
                                             followup=save_followup_no))

        await menu.update(confirm_page, confirm_buttons)

    else:
        await cancel_edition_yes(menu, edit_variables, data_pages, data_buttons)


async def cancel_edition_yes(menu, edit_variables, data_pages, data_buttons):
    menu.show_page_director = False
    menu.edited = False
    for variable in edit_variables:
        setattr(menu.item, variable['name'], variable['first_value'])
    await menu.update(data_pages, data_buttons)

async def cancel_edition_no(menu, edit_pages, edit_buttons):
    menu.show_page_director = True
    await menu.update(edit_pages, edit_buttons)

async def cancel_edition(menu, edit_variables, data_pages, data_buttons, edit_pages, edit_buttons):
    if menu.edited:
        menu.show_page_director = False
        confirm_page = [discord.Embed(title="Cancelar", colour=discord.Colour.blue(),
                                  description="¿Está seguro de que desea cancelar? \
                                  Se perderán todos los cambios realizados.")]
        confirm_buttons = []

        cancel_followup_no = ComponentsButton.Followup()
        cancel_followup_no.set_caller_details(cancel_edition_no, menu, edit_pages, edit_buttons)
        confirm_buttons.append(ComponentsButton(style=ComponentsButton.style.green, label='Seguir editando',
                                             custom_id=ComponentsButton.ID_CALLER,
                                             followup=cancel_followup_no))

        cancel_followup_yes = ComponentsButton.Followup()
        cancel_followup_yes.set_caller_details(cancel_edition_yes, menu, edit_variables, 
                                               data_pages, data_buttons)
        confirm_buttons.append(ComponentsButton(style=ComponentsButton.style.red, label='Cancelar',
                                             custom_id=ComponentsButton.ID_CALLER,
                                             followup=cancel_followup_yes))

        await menu.update(confirm_page, confirm_buttons)

    else:
        await cancel_edition_yes(menu, edit_variables, data_pages, data_buttons)

async def cancel_value_edition(menu, edit_pages, edit_buttons, page_index):
    menu.show_page_director = True
    await menu.update(edit_pages, edit_buttons)
    menu._pc.index = page_index
    await menu.message.edit(embed=menu._pc.current_page)    
    
async def apply_value_edition(menu, field, value, edit_pages, edit_buttons, page_index):
    setattr(menu.item, field['name'], value)
    menu.edited = True
    menu.show_page_director = True
    edit_pages.clear()
    session = Session()
    for page in get_edit_pages(menu, session)[0]:
        edit_pages.append(page)
    session.close()    
    await menu.update(edit_pages, edit_buttons)
    menu._pc.index = page_index
    await menu.message.edit(embed=menu._pc.current_page)   

async def edit_value(menu, edit_variables, edit_pages, edit_buttons):
    menu.show_page_director = False
    page_index = menu._pc.index
    field = edit_variables[page_index]
    
    fk = None
    try:
        fk = field['fk']
        session = Session()
        foreign = session.query(fk.table).filter(fk.table.columns['id'] == getattr(menu.item, field['name'])).first()
        session.close()
        original_value = foreign.name if foreign is not None else 'Ninguno'
    except:
        original_value = getattr(menu.item, field['name'], 'Ninguno')
        
    desc = f"Introduzca un nuevo valor para {field['disp_name']} en {menu.item.short_str()}\n\
    Tipo de propiedad: {models.type_names[field['type']]}\n\
    Valor actual: {original_value}"
    
    value_page = [discord.Embed(title=f"Modificando {field['disp_name']}", colour=discord.Colour.blue(),
                                  description=desc)]    
    confirm_buttons = []
    apply_followup = ComponentsButton.Followup()
    confirm_buttons.append(ComponentsButton(style=ComponentsButton.style.green, label='Aceptar',
                                     custom_id=ComponentsButton.ID_CALLER,
                                     followup=apply_followup))
    
        
    cancel_followup = ComponentsButton.Followup()
    cancel_followup.set_caller_details(cancel_value_edition, menu, edit_pages, edit_buttons, page_index)
    confirm_buttons.append(ComponentsButton(style=ComponentsButton.style.red, label='Cancelar',
                                             custom_id=ComponentsButton.ID_CALLER,
                                             followup=cancel_followup))
    
    await menu.update(value_page, confirm_buttons)
    menu.disable_all_buttons()
    await menu.refresh_menu_buttons()
    
    success = False
    
    while not success:    
        try:            
            user_response = await menu._bot.wait_for('message', check=lambda m: m.channel.id == menu.message.channel.id 
                                               and m.author.id == menu._ctx.author.id, timeout=menu.timeout)
            value = (user_response.content)                
            if menu.delete_interactions:
                await user_response.delete()
                
            if value == 'Ninguno':
                value = None
            else:
                if field['type'] == int:
                    value = ''.join([c for c in value if c.isdigit()])
                value = field['type'](value)
            
            if fk is not None and value is not None:
                session = Session()
                target = session.query(fk.table).filter(fk.table.columns['name'].ilike(f'%{value}%')).first()
                session.close()
                if target is None:
                    raise ValueError
                else:
                    value = target.id
                
        except TimeoutError:
            continue
        except ValueError:
            await menu.update([discord.Embed(title=f"Modificando {field['disp_name']}", colour=discord.Colour.blue(),
                                      description=desc+"\n\nValor incorrecto, inténtelo de nuevo.")], None)
            continue
        else:
            success = True
            display_value = 'Ninguno' if value is None else (value if fk is None else target.name)
            confirm_page = [discord.Embed(title=f"Modificando {field['disp_name']}", colour=discord.Colour.blue(),
                                      description=f"El nuevo valor de {field['disp_name']} \
                                      en {menu.item.short_str()} es:\n\n{display_value}\n\n¿Aceptar?")]
            
            apply_followup.set_caller_details(apply_value_edition, menu, field, value,
                                              edit_pages, edit_buttons, page_index)
            menu.enable_all_buttons()            
            await menu.update(confirm_page, None)

def get_edit_pages(menu, session):
    edit_pages = []
    edit_variables = []
    item_class = type(menu.item)
    columns = []
    
    if issubclass(item_class, models.Character) and menu.item.id is not None:
        if menu.model_class != item_class:
            menu.item = session.query(item_class).filter(item_class.id == menu.item.id).first()
            menu.model_class = item_class
        columns = models.Character.__table__.c + item_class.__table__.c       
    else:
        columns = item_class.__table__.c
    
    for column in columns:
        if column.primary_key:
            continue
        elif len(column.foreign_keys) > 0:
            fk = next(iter(column.foreign_keys)).column
            foreign = session.query(fk.table).filter(fk.table.columns['id'] == getattr(menu.item, column.name)).first()
            foreign_name = foreign.name if foreign is not None else 'Ninguno'
            #foreign = session.query(fk.table).filter(fk.table.columns['id'] == 5).first()
            content = f"**Propiedad**\n\
            {column.comment}\n\
            \n\
            **Tipo de propiedad**\n\
            {models.type_names[str]}\n\
            \n\
            **Valor**\n\
            {foreign_name}"
            edit_pages.append(discord.Embed(title=f"{menu.item.short_str()}", colour=discord.Colour.blue(),
                              description=content))
            edit_variables.append({'name':column.name, 'disp_name':column.comment, 
                                   'type':str, 'fk':fk, 'first_value':getattr(menu.item, column.name, None)})
        else:
            content = f"**Propiedad**\n\
            {column.comment}\n\
            \n\
            **Tipo**\n\
            {models.type_names[column.type.python_type]}\n\
            \n\
            **Valor**\n\
            {getattr(menu.item, column.name, 'Ninguno')}"
            edit_pages.append(discord.Embed(title=f"{menu.item.short_str()}", colour=discord.Colour.blue(),
                              description=content))
            edit_variables.append({'name':column.name, 'disp_name':column.comment, 
                                   'type':column.type.python_type, 'first_value':getattr(menu.item, column.name, None)})
    return edit_pages, edit_variables

async def insert_basic_traits(menu):
    blood_traits = ['Reserva de sangre']
    ni_traits = ['Disciplina', 'Trasfondo', 'Mérito', 'Defecto', 'Especial']
    sucks_blood = type(menu.item) in [models.Vampire, models.Ghoul]
    session = Session()
    basic_traits = session.query(models.Trait).filter(models.Trait.tier == 1).all()
    for trait in basic_traits:
        if trait.trait_type.name in ni_traits:
            continue
        if trait.trait_type.name in blood_traits and not sucks_blood:
            continue
            
        character_trait = models.CharacterTrait(character_id = menu.item.id, trait_id = trait.id, value = trait.default_value)
        session.add(character_trait)
    session.commit()
    menu.item = session.query(models.Character).options(
                joinedload(models.Character.traits).joinedload(models.CharacterTrait.trait)).filter(
                models.Character.id == menu.item.id).first()     
    session.close()
    
async def edit_traits(menu):
    count = len(menu.item.traits)
    traits_menu = None
    if count == 0:
        await insert_basic_traits(menu)
    
    traits_menu = ButtonsMenu(menu._ctx, menu_type=ButtonsMenu.TypeEmbedDynamic, rows_requested = 10,
                  custom_embed=discord.Embed(title=f'Rasgos de {menu.item.name}', colour=discord.Colour.blue()),
                  style="Página $ de &")
    traits_menu.model_class = models.CharacterTrait
    traits_menu.item = menu.item
    await init_menu_from_table(traits_menu, rows = menu.item.traits)
    await traits_menu.start()
    traits_menu.set_relay(traits_menu_listener)
    await traits_refresh_buttons(traits_menu)
    await menu.stop(delete_menu_message=True)
    
async def edit_item(menu):
    menu.edited = False
    session = Session()
    data_pages = menu._ButtonsMenu__pages
    data_buttons = [i for i in menu.buttons]
    
    edit_buttons = []
    edit_pages, edit_variables = get_edit_pages(menu, session)
    
    session.close()
    
    edit_followup = ComponentsButton.Followup()
    edit_followup.set_caller_details(edit_value, menu, edit_variables, edit_pages, edit_buttons)
    edit_buttons.append(ComponentsButton(style=ComponentsButton.style.green, label='Modificar',
                                         custom_id=ComponentsButton.ID_CALLER,
                                         followup=edit_followup))
    
    n_pages = len(edit_pages)
    if n_pages > 1:
        edit_buttons.append(ComponentsButton(style=ComponentsButton.style.primary, label='Página Anterior',
                                           custom_id=ComponentsButton.ID_PREVIOUS_PAGE))
        edit_buttons.append(ComponentsButton(style=ComponentsButton.style.primary, label='Página Siguiente',
                                           custom_id=ComponentsButton.ID_NEXT_PAGE))
        if n_pages > 3:
            edit_buttons.append(ComponentsButton(style=ComponentsButton.style.primary, label='Seleccionar Página',
                                               custom_id=ComponentsButton.ID_GO_TO_PAGE))
            
    save_followup = ComponentsButton.Followup()
    save_followup.set_caller_details(save_edition, menu, edit_variables, data_pages, data_buttons, 
                                       edit_pages, edit_buttons)
    edit_buttons.append(ComponentsButton(style=ComponentsButton.style.green, label='Guardar cambios',
                                         custom_id=ComponentsButton.ID_CALLER,
                                         followup=save_followup))
    
    cancel_followup = ComponentsButton.Followup()
    cancel_followup.set_caller_details(cancel_edition, menu, edit_variables, data_pages, data_buttons, 
                                       edit_pages, edit_buttons)
    edit_buttons.append(ComponentsButton(style=ComponentsButton.style.red, label='Cancelar',
                                         custom_id=ComponentsButton.ID_CALLER,
                                         followup=cancel_followup))
    menu.show_page_director = True
    menu.style = "Página $ de &"
    await menu.update(edit_pages, edit_buttons)
    
async def delete_yes(menu):
    session = Session()
    session.delete(menu.item)
    session.commit()
    session.close()
    del menu.item
    after_pages = [discord.Embed(title="Eliminado", colour=discord.Colour.blue(),
                                  description="El elemento ha sido eliminado con éxito.")]
    after_buttons = [ComponentsButton(style=ComponentsButton.style.primary, label='Cerrar',
                                         custom_id=ComponentsButton.ID_END_SESSION)]
    
    await menu.update(after_pages, after_buttons)
    
async def delete_no(menu, data_pages, data_buttons):
    await menu.update(data_pages, data_buttons)

async def delete_item(menu):
    data_pages = menu._ButtonsMenu__pages
    data_buttons = [i for i in menu.buttons]
    
    confirm_page = [discord.Embed(title="Eliminar", colour=discord.Colour.blue(),
                                  description=f"¿Está seguro de que desea eliminar **{menu.item.short_str()}**? \
                                  Una vez eliminado, no es posible recuperarlo.")]
    confirm_buttons = []

    followup_no = ComponentsButton.Followup()
    followup_no.set_caller_details(delete_no, menu, data_pages, data_buttons)
    confirm_buttons.append(ComponentsButton(style=ComponentsButton.style.green, label='No eliminar',
                                         custom_id=ComponentsButton.ID_CALLER,
                                         followup=followup_no))
    
    followup_yes = ComponentsButton.Followup()
    followup_yes.set_caller_details(delete_yes, menu)
    confirm_buttons.append(ComponentsButton(style=ComponentsButton.style.red, label='Eliminar',
                                         custom_id=ComponentsButton.ID_CALLER,
                                         followup=followup_yes))
    await menu.update(confirm_page, confirm_buttons)
    
async def init_menu_from_item(menu, session=None, filters = None, item = None):
    if item is None:
        item = read_from_table(menu.model_class, session, True, filters)    
    if item is None:
        menu.add_page(discord.Embed(description='Elemento no encontrado', colour=discord.Colour.blue()))
    else:
        menu.item = item
        menu.add_page(discord.Embed(title=item.short_str(), description=str(item), colour=discord.Colour.blue()))
        if is_admin(menu.owner):
            edit_followup = ComponentsButton.Followup()
            edit_followup.set_caller_details(edit_item, menu)
            menu.add_button(ComponentsButton(style=ComponentsButton.style.green, label='Editar',
                                     custom_id=ComponentsButton.ID_CALLER, followup=edit_followup)) 
            if menu.model_class in [models.Character, models.Vampire, models.Ghoul] and menu.item.id is not None:
                traits_followup = ComponentsButton.Followup()
                traits_followup.set_caller_details(edit_traits, menu)
                menu.add_button(ComponentsButton(style=ComponentsButton.style.green, label='Editar rasgos',
                                         custom_id=ComponentsButton.ID_CALLER, followup=traits_followup))
            delete_followup = ComponentsButton.Followup()
            delete_followup.set_caller_details(delete_item, menu)
            menu.add_button(ComponentsButton(style=ComponentsButton.style.red, label='Eliminar',
                                     custom_id=ComponentsButton.ID_CALLER, followup=delete_followup))

    menu.add_button(ComponentsButton(style=ComponentsButton.style.primary, label='Cerrar',
                                     custom_id=ComponentsButton.ID_END_SESSION))
    
async def init_menu_from_table(menu, session = None, filters = None, rows = None):    
    if rows is None:
        rows = read_from_table(menu.model_class, session, False, filters)
    count = len(rows)
    if count == 0:
        menu.add_row("No se encontraron elementos.")
    else:
        for i, row in zip(range(1, len(rows)+1), rows):
            menu._bypass_primed = True
            menu.add_row(f"{i} - {row.short_str()}")
        menu.set_relay(table_menu_listener)
        
    menu.add_button(ComponentsButton(style=ComponentsButton.style.primary, label='Cerrar',
                                     custom_id=ComponentsButton.ID_END_SESSION))
    

            
class Data(commands.Cog, name = 'Datos'):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name='find', aliases=['buscar'])
    async def read_by_name(self, ctx, table:str, *, name=''):
        if len(name) == 0:
            await ctx.invoke(self.bot.get_command('data'), args=table)
        else:
            model_class = models.get_model_class(table)
            if model_class is None:
                await ctx.send(f'{table} no se reconoce en la base de datos')
            else:
                session = Session()
                rows = read_from_table(model_class['class'], session, False, filters = [model_class['class'].name.ilike(f'%{name}%')])
                count = len(rows)
                menu = None
                if count == 1:
                    model_class = model_class['class']
                    if type(rows[0]) != model_class:
                        model_class = type(rows[0])
                        rows = read_from_table(model_class, session, False, filters = [model_class.name.ilike(f'%{name}%')])  
                    session.close()
                    menu = ButtonsMenu(ctx, menu_type=ButtonsMenu.TypeEmbed, show_page_director=False, timeout=300)
                    menu.model_class = model_class
                    await init_menu_from_item(menu, item = rows[0])
                    await menu.start()
                else: 
                    session.close()
                    menu = ButtonsMenu(ctx, menu_type=ButtonsMenu.TypeEmbedDynamic, rows_requested = 10,
                                  custom_embed=discord.Embed(title=model_class['p_name'], colour=discord.Colour.blue()),
                                  style="Página $ de &")
                    menu.model_class = model_class['class']
                    await init_menu_from_table(menu, rows = rows)
                    await menu.start() 
                    await table_refresh_buttons(menu)
        
    @commands.command(name='data', aliases=['d', 'list', 'all'])
    async def read_all(self, ctx, *, args):
        model_class = models.get_model_class(args)
        if model_class is None:
            await ctx.send(f'{args} no se reconoce en la base de datos')

        else:    
            menu = ButtonsMenu(ctx, menu_type=ButtonsMenu.TypeEmbedDynamic, rows_requested = 10,
                              custom_embed=discord.Embed(title=model_class['p_name'], colour=discord.Colour.blue()),
                              style="Página $ de &")
            menu.model_class = model_class['class']
            session = Session()            
            await init_menu_from_table(menu, session)
            session.close()        

            await menu.start()    
            await table_refresh_buttons(menu)
            

    @commands.command(name='trait', aliases=['get', 'traits', 'character', 'char', 'c'])
    async def get_traits(self, ctx, character_name:str, *, trait_name=''):
        if trait_name == '':
            await ctx.invoke(self.bot.get_command('find'), table='character', name=character_name)
        else:
            session = Session()
            character = session.query(models.Character).filter(models.Character.name.ilike(f'%{character_name}%')).first()
            if character is None:
                await ctx.send(embed = discord.Embed(description = f"Personaje **{character_name}** no encontrado.",
                                                     colour=discord.Colour.blue()))
            else:      
                traits = session.query(models.Trait).filter(models.Trait.name.ilike(f'%{trait_name}%')).limit(10).all()
                if len(traits) == 0:
                    await ctx.send(embed = discord.Embed(title=f"{character.name}",
                                                         description = f"Rasgo **{trait_name}** no encontrado.",
                                                         colour=discord.Colour.blue()))
                else:
                    character_traits = []
                    for trait in traits:
                        character_trait = session.query(models.CharacterTrait).filter(
                            models.CharacterTrait.character_id == character.id, 
                            models.CharacterTrait.trait_id == trait.id).first()
                        if character_trait is not None:
                            character_traits.append(character_trait)
                            
                    if len(character_traits) == 0:
                        embed = discord.Embed(title=f"{character.name}",
                                              description = f"**{character.name}** no posee el rasgo **{trait_name}**.",
                                              colour=discord.Colour.blue())
                        await ctx.send(embed = embed)
                    else:
                        desc = "\n".join([ct.short_str() for ct in character_traits])
                        await ctx.send(embed = discord.Embed(title=f"{character.name}",
                                                             description = desc,
                                                         colour=discord.Colour.blue()))
            session.close()
    