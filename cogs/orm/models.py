from sqlalchemy import ForeignKey, Sequence
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.expression import case
from sqlalchemy.sql import select
from datetime import datetime

Base = declarative_base()

_new_name = lambda: f"Nuevo ({datetime.now().strftime('%Y/%d/%m %H:%M:%S')})"

class Character(Base):
    __tablename__ = "character"
    id = Column(Integer, Sequence('character_id_seq'), primary_key=True, comment='ID de personaje')
    character_type_id = Column(Integer, ForeignKey('character_type.id'), 
                               comment='Tipo de personaje', default=1)
    player_id = Column(Integer, comment='Jugador', default=0)    
    name = Column(String, unique = True, comment='Nombre', default=_new_name())
    race_id = Column(Integer, ForeignKey('race.id'), comment='Raza', default=1) 
    nature_id = Column(Integer, ForeignKey('archetype.id'), comment='Naturaleza', default=1) 
    demeanor_id = Column(Integer, ForeignKey('archetype.id'), comment='Conducta', default=1) 
    gender = Column(String, comment='Género', default='Masculino')
    concept = Column(String, comment='Concepto', default='Iniciado')
    activity = Column(Integer, comment='Actividad', default=1)
    notes = Column(String, comment='Notas')
    public = Column(Integer, comment='Público', default=1)
    
    character_type = relationship("CharacterType", back_populates="characters")
    race = relationship("Race", back_populates="characters")
    nature = relationship("Archetype", foreign_keys=[nature_id], back_populates="nature_characters")
    demeanor = relationship("Archetype", foreign_keys=[demeanor_id], back_populates="demeanor_characters")
    traits = relationship("CharacterTrait", cascade="all, delete-orphan")    
    
    __mapper_args__ = {
        'polymorphic_identity':"character",
        "polymorphic_on":case([
            (race_id == 1, "vampire"),
            (race_id == 2, "ghoul")
        ], else_="character")
    }
    
    def short_str(self):
        if self.name is None:
            return "Sin nombre"
        return self.name
    
    def __str__(self):
        if self.name is None:
            return "No hay datos."
        
        return f"""{'*Personaje privado*' if self.public == 0 else ''}
**Tipo:** {self.character_type.name}
**Propietario:** <@{self.player_id}>
**Raza:** {self.race.name}
**Género:** {self.gender}
**Naturaleza:** {self.nature.name}
**Conducta:** {self.demeanor.name}
**Concepto:** {self.concept}
**Actividad:** {'Activo' if self.activity == 1 else 'Inactivo'}

**Físicos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Atributo Físico')])}
**Sociales:** {', '.join([trait.minimal_str() for trait in self.get_traits('Atributo Social')])}
**Mentales:** {', '.join([trait.minimal_str() for trait in self.get_traits('Atributo Mental')])}

**Talentos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Talento')])}
**Técnicas:** {', '.join([trait.minimal_str() for trait in self.get_traits('Técnica')])}
**Conocimientos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Conocimiento')])}

**Trasfondos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Trasfondo')])}

**Virtudes:** {', '.join([trait.minimal_str() for trait in self.get_traits('Virtud')])}
**Moralidad:** {', '.join([trait.minimal_str() for trait in self.get_traits('Moralidad')])}
**Fuerza de voluntad:** {self.wp_str()} 

**Méritos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Mérito')])}
**Defectos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Defecto')])}

**Salud:** {self.health_str()} 

{self.notes if self.notes is not None else ''}"""
    
    def wp_str(self):        
        pwp = self.get_traits(trait_name='Fuerza de Voluntad (permanente)')
        wp = self.get_traits(trait_name='Fuerza de Voluntad (temporal)')
        return f"{wp.value} / {pwp.value}" if (wp is not None and pwp is not None) else ""    
    
    def health_str(self):        
        mhealth = self.get_traits(trait_name='Salud (máxima)')
        health = self.get_traits(trait_name='Salud (actual)')
        
        if health is None or mhealth is None:
            return ""
        
        result = f"{health.value} / {mhealth.value}"
        
        agg = self.get_traits(trait_name='Daño agravado')
        if agg is None:
            agg = 0
        else:
            agg = agg.value
            
        leth = self.get_traits(trait_name='Daño letal')
        if leth is None:
            leth = 0
        else:
            leth = leth.value
            
        damage = []
        if leth > 0:
            damage.append(f"{leth} letal")
        if agg > 0:
            damage.append(f"{agg} agravado")
            
        result = f"{result} ({', '.join(damage)})" if len(damage) > 0 else result
        
        return result
    
    def blood_str(self):        
        mpool = self.get_traits(trait_name='Reserva de sangre (máxima)')
        pool = self.get_traits(trait_name='Reserva de sangre (actual)')
        return f"{pool.value} / {mpool.value}" if (pool is not None and mpool is not None) else ""
    
    def get_traits(self, trait_type=None, trait_name=None):
        if trait_type is not None:
            return [trait for trait in self.traits if trait.trait.trait_type.name == trait_type]
        elif trait_name is not None:
            traits = [trait for trait in self.traits if trait.trait.name == trait_name]
            return traits[0] if len(traits) == 1 else None            
        else:
            return self.traits
    
class CharacterType(Base):
    __tablename__ = "character_type"
    id = Column(Integer, Sequence('character_type_id_seq'), primary_key=True, comment='ID de tipo de personaje')
    name = Column(String, unique = True, comment='Nombre', default=_new_name())
    description = Column(String, comment='Descripción')
    
    characters = relationship("Character", order_by=Character.id, back_populates="character_type")
    
    def short_str(self):
        if self.name is None:
            return "Sin nombre"
        return self.name
    
    def __str__(self):
        if self.name is None:
            return "No hay datos."
        return self.description
    
class Race(Base):
    __tablename__ = "race"
    id = Column(Integer, Sequence('race_id_seq'), primary_key=True, comment='ID de raza')
    name = Column(String, unique = True, comment='Nombre', default=_new_name())
    description = Column(String, comment='Descripción')
    blood_loss = Column(Integer, comment='Intervalo de pérdida de sangre')
    
    characters = relationship("Character", order_by=Character.id, back_populates="race")
    
    def short_str(self):
        if self.name is None:
            return "Sin nombre"
        return self.name
    
    def __str__(self):
        if self.name is None:
            return "No hay datos."
        return self.description

class Archetype(Base):
    __tablename__ = "archetype"
    id = Column(Integer, Sequence('archetype_id_seq'), primary_key=True, comment='ID de arquetipo')
    name = Column(String, unique = True, comment='Nombre', default=_new_name())
    description = Column(String, comment='Descripción')
    
    nature_characters = relationship("Character", foreign_keys='Character.nature_id', 
                                     order_by=Character.id, back_populates="nature")
    demeanor_characters = relationship("Character", foreign_keys='Character.demeanor_id', 
                                       order_by=Character.id, back_populates="demeanor")
    
    def short_str(self):
        if self.name is None:
            return "Sin nombre"
        return self.name
    
    def __str__(self):
        if self.name is None:
            return "No hay datos."
        return self.description
    
class Vampire(Character):
    __tablename__ = "vampire"
    id = Column(Integer, ForeignKey('character.id'), primary_key=True, comment='ID de personaje')
    clan_id = Column(Integer, ForeignKey('clan.id'), comment='Clan', default=1) 
    generation_id = Column(Integer, ForeignKey('generation.id'), comment='Generación', default=10) 
    sire = Column(String, comment='Sire', default='Nadie')
    curse_spec = Column(String, comment='Especificaciones de maldición de clan')
    
    clan = relationship("Clan", back_populates="vampires")
    generation = relationship("Generation", back_populates="vampires")
    
    __mapper_args__ = {
        'polymorphic_identity':'vampire',
    }
    
    def __str__(self):
        if self.name is None:
            return "No hay datos."
        return f"""{'*Personaje privado*' if self.public == 0 else ''}
**Tipo:** {self.character_type.name}
**Propietario:** <@{self.player_id}>
**Raza:** {self.race.name}
**Clan:** {self.clan.name}
**Generación:** {self.generation.name}
**Sire:** {self.sire}
**Género:** {self.gender}
**Naturaleza:** {self.nature.name}
**Conducta:** {self.demeanor.name}
**Concepto:** {self.concept}
**Actividad:** {'Activo' if self.activity == 1 else 'Inactivo'}

**Físicos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Atributo Físico')])}
**Sociales:** {', '.join([trait.minimal_str() for trait in self.get_traits('Atributo Social')])}
**Mentales:** {', '.join([trait.minimal_str() for trait in self.get_traits('Atributo Mental')])}

**Talentos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Talento')])}
**Técnicas:** {', '.join([trait.minimal_str() for trait in self.get_traits('Técnica')])}
**Conocimientos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Conocimiento')])}

**Disciplinas:** {', '.join([trait.minimal_str() for trait in self.get_traits('Disciplina')])}
**Trasfondos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Trasfondo')])}

**Virtudes:** {', '.join([trait.minimal_str() for trait in self.get_traits('Virtud')])}
**Moralidad:** {', '.join([trait.minimal_str() for trait in self.get_traits('Moralidad')])}
**Fuerza de voluntad:** {self.wp_str()} 

**Méritos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Mérito')])}
**Defectos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Defecto')])}        

**Salud:** {self.health_str()} 
**Reserva de sangre:** {self.blood_str()} 

**Debilidad de clan:** {self.clan.curse} {'('+self.curse_spec+')' if self.curse_spec is not None else ''}

{self.notes if self.notes is not None else ''}
                """
    
class Ghoul(Character):
    __tablename__ = "ghoul"
    id = Column(Integer, ForeignKey('character.id'), primary_key=True, comment='ID de personaje')
    clan_id = Column(Integer, ForeignKey('clan.id'), comment='Clan', default=1) 
    generation_id = Column(Integer, ForeignKey('generation.id'), comment='Generación', default=10)
    ghoul_type_id = Column(Integer, ForeignKey('ghoul_type.id'), comment='Tipo de Ghoul', default=1)
    domitor = Column(String, comment='Domitor', default='Nadie')
    curse_spec = Column(String, comment='Especificaciones de maldición de clan')
    
    clan = relationship("Clan", back_populates="ghouls")
    generation = relationship("Generation", back_populates="ghouls")
    ghoul_type = relationship("GhoulType", back_populates="ghouls")
    
    __mapper_args__ = {
        'polymorphic_identity':'ghoul',
    }
    
    def __str__(self):
        if self.name is None:
            return "No hay datos."
        return f"""{'*Personaje privado*' if self.public == 0 else ''}
**Tipo:** {self.character_type.name}
**Propietario:** <@{self.player_id}>
**Raza:** {self.race.name}
**Tipo de Ghoul:** {self.ghoul_type.name}
**Clan:** {self.clan.name}
**Generación:** {self.generation.name}
**Domitor:** {self.domitor}        
**Género:** {self.gender}
**Naturaleza:** {self.nature.name}
**Conducta:** {self.demeanor.name}
**Concepto:** {self.concept}
**Actividad:** {'Activo' if self.activity == 1 else 'Inactivo'}

**Físicos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Atributo Físico')])}
**Sociales:** {', '.join([trait.minimal_str() for trait in self.get_traits('Atributo Social')])}
**Mentales:** {', '.join([trait.minimal_str() for trait in self.get_traits('Atributo Mental')])}

**Talentos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Talento')])}
**Técnicas:** {', '.join([trait.minimal_str() for trait in self.get_traits('Técnica')])}
**Conocimientos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Conocimiento')])}

**Disciplinas:** {', '.join([trait.minimal_str() for trait in self.get_traits('Disciplina')])}
**Trasfondos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Trasfondo')])}

**Virtudes:** {', '.join([trait.minimal_str() for trait in self.get_traits('Virtud')])}
**Moralidad:** {', '.join([trait.minimal_str() for trait in self.get_traits('Moralidad')])}
**Fuerza de voluntad:** {self.wp_str()} 

**Méritos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Mérito')])}
**Defectos:** {', '.join([trait.minimal_str() for trait in self.get_traits('Defecto')])}        

**Salud:** {self.health_str()} 
**Reserva de sangre:** {self.blood_str()}

**Debilidad de clan:** {self.clan.curse} {'('+self.curse_spec+')' if self.curse_spec is not None else ''}

{self.notes if self.notes is not None else ''}"""
    
    
    
class GhoulType(Base):
    __tablename__ = "ghoul_type"
    id = Column(Integer, Sequence('ghoul_type_id_seq'), primary_key=True, comment='ID de tipo de Ghoul')
    name = Column(String, unique = True, comment='Nombre', default=_new_name())
    description = Column(String, comment='Descripción')
    
    ghouls = relationship("Ghoul", order_by=Ghoul.id, back_populates="ghoul_type")
    
    def short_str(self):
        if self.name is None:
            return "Sin nombre"
        return self.name
    
    def __str__(self):
        if self.name is None:
            return "No hay datos."
        return self.description
    
class Generation(Base):
    __tablename__ = "generation"
    id = Column(Integer, Sequence('generation_id_seq'), primary_key=True, comment='ID de generación')
    number = Column(Integer, unique = True, comment='Número')
    name = Column(String, unique = True, comment='Nombre', default=_new_name())
    description = Column(String, comment='Descripción')
    trait_cap = Column(Integer, comment='Máximo valor de rasgos')
    pool = Column(Integer, comment='Reserva de sangre')
    blood_per_turn = Column(Integer, comment='Gasto máximo de sangre por turno')
    
    vampires = relationship("Vampire", order_by=Vampire.id, back_populates="generation")
    ghouls = relationship("Ghoul", order_by=Ghoul.id, back_populates="generation")
    
    def short_str(self):
        if self.name is None:
            return "Sin nombre"
        return self.name + " Generación"
    
    def __str__(self):
        if self.name is None:
            return "No hay datos."
        return f"""{self.description}

**Máximo valor de rasgos:** {self.trait_cap}
**Reserva de sangre:** {self.pool}
**Gasto máximo de sangre por turno:** {self.blood_per_turn}
"""
    
class Clan(Base):
    __tablename__ = "clan"
    id = Column(Integer, Sequence('clan_id_seq'), primary_key=True, comment='ID de clan')
    name = Column(String, unique = True, comment='Nombre', default=_new_name())
    description = Column(String, comment='Descripción')
    curse = Column(String, comment='Debilidad de clan')
    
    vampires = relationship("Vampire", order_by=Vampire.id, back_populates="clan")
    ghouls = relationship("Ghoul", order_by=Ghoul.id, back_populates="clan")
    
    def short_str(self):
        if self.name is None:
            return "Sin nombre"
        return self.name
    
    def __str__(self):
        if self.name is None:
            return "No hay datos."
        return f"""{self.description}

**Debilidad de clan:** {self.curse}"""
    
class Trait(Base):
    __tablename__ = "trait"
    id = Column(Integer, Sequence('trait_id_seq'), primary_key=True, comment='ID de rasgo')
    trait_type_id = Column(Integer, ForeignKey('trait_type.id'), comment='Tipo de rasgo')
    parent_id = Column(Integer, ForeignKey(id), comment='Rasgo superior')
    name = Column(String, unique = True, comment='Nombre', default=_new_name())
    description = Column(String, comment='Descripción')
    default_value = Column(Integer, comment='Valor por defecto')
    tier = Column(Integer, comment='Categoría')
    
    trait_type = relationship("TraitType", back_populates="traits")
    #parent = relationship("Trait", back_populates="children")
    
    children = relationship(
        "Trait",
        # cascade deletions
        cascade="all, delete-orphan",
        # many to one + adjacency list - remote_side
        # is required to reference the 'remote'
        # column in the join condition.
        backref=backref("parent", remote_side=id)
    )
    
    def short_str(self):
        if self.name is None:
            return "Sin nombre"
        return self.name
    
    def __str__(self):
        if self.name is None:
            return "No hay datos."
        return f"""**Tipo de rasgo:** {self.trait_type.name if self.trait_type_id is not None else 'Ninguno'}
**Categoría:** {'Primario' if self.tier == 1 else ('Secundario' if self.tier == 2 else 'Personalizado')}
**Valor por defecto:** {self.default_value}

{self.description}"""
    
class TraitType(Base):
    __tablename__ = "trait_type"
    id = Column(Integer, Sequence('trait_type_id_seq'), primary_key=True, comment='ID de tipo de rasgo')
    name = Column(String, unique = True, comment='Nombre', default=_new_name())
    description = Column(String, comment='Descripción')
    generation_capped = Column(Integer, comment='Limitado por generación')
    
    traits = relationship("Trait", order_by=Trait.id, back_populates="trait_type")
    
    def short_str(self):
        if self.name is None:
            return "Sin nombre"
        return self.name
    
    def __str__(self):
        if self.name is None:
            return "No hay datos."
        trait_list = '*Ninguno*'
        trait_count = len(self.traits)   
        if trait_count > 0:
            trait_list = ', '.join([i.name for i in self.traits][:5])
            if trait_count > 5:
                trait_list += f"... ({trait_count-5} más)"
                               
        return f"""{self.description}
**Limitado por generación:** {'Sí' if self.generation_capped == 1 else 'No'}
**Rasgos:** {trait_list}"""
    
class CharacterTrait(Base):
    __tablename__ = "character_trait"
    character_id = Column(Integer, ForeignKey('character.id'), primary_key=True, comment='ID de personaje')
    trait_id = Column(Integer, ForeignKey('trait.id'), primary_key=True, comment='ID de rasgo')
    value = Column(Integer, comment='Valor')
    # server_default=f"SELECT trait.default_value FROM trait WHERE trait.id = {trait_id}"
    # default=select([Trait.__table__.c.default_value]).where(Trait.__table__.c.id == trait_id)
    specs = Column(String, comment='Especialidad / Especificación')
    
    trait = relationship("Trait")
    
    def minimal_str(self, show_specs = True):
        value = f"{self.trait.name} {self.value_str(1)}"
        if show_specs and self.specs is not None:
            specs_str = self.specs if len(self.specs) < 30 else self.specs[:27] + "..."
            value += f" ({specs_str})"
        return value
    
    def short_str(self):
        value = f"{self.trait.name}: {self.value_str(1)}"
        if self.specs is not None:
            specs_str = self.specs if len(self.specs) < 30 else self.specs[:27] + "..."
            specs_str = specs_str.replace(':', '')
            value += f" ({specs_str})"
        return value
    
    def __str__(self):
        return f"""Valor: {self.value_str()}

Especialidad / Especificación: {self.specs if self.specs is not None else 'Ninguna'}"""
    
    def value_str(self, size=0):
        if size == 0:
            size = 2 if self.value < 11 else 1
        return {1: str(self.value),
                2: f"{' '.join(['O' for i in range(self.value)])}"}[size]
                
    
model_classes=[
    {'class':Character, 's_name':'Personaje', 'p_name':'Personajes', 'aliases':[
        'char', 'character', 'chars', 'characters', 'c'
    ]},
    {'class':CharacterType, 's_name':'Tipo de personaje', 'p_name':'Tipos de personaje', 'aliases':[
        'chartypes', 'character types', 'chartype', 'character type', 'charactertype', 'charactertypes'
    ]},
    {'class':Race, 's_name':'Raza', 'p_name':'Razas', 'aliases':[
        'race', 'races'
    ]},
    {'class':Archetype, 's_name':'Arquetipo de personalidad', 'p_name':'Arquetipos de personalidad', 'aliases':[
        'archetype', 'archetypes', 'arquetipo', 'arquetipos', 'naturaleza', 'naturalezas', 'conducta', 'conductas',
        'nature', 'natures', 'demeanor', 'demeanors'
    ]},
    {'class':Vampire, 's_name':'Vampiro', 'p_name':'Vampiros', 'aliases':[
        'vampire', 'vampires'
    ]},
    {'class':Ghoul, 's_name':'Ghoul', 'p_name':'Ghouls', 'aliases':[
        
    ]},
    {'class':GhoulType, 's_name':'Tipo de Ghoul', 'p_name':'Tipos de Ghoul', 'aliases':[
        'ghoul type', 'ghoul types', 'ghoultype', 'ghoultypes'
    ]},
    {'class':Generation, 's_name':'Generación', 'p_name':'Generaciones', 'aliases':[
        'generation', 'generations', 'generacion'
    ]},
    {'class':Clan, 's_name':'Clan', 'p_name':'Clanes', 'aliases':[
        'clans'
    ]},
    {'class':Trait, 's_name':'Rasgo', 'p_name':'Rasgos', 'aliases':[
        'trait', 'traits'
    ]},
    {'class':TraitType, 's_name':'Tipo de rasgo', 'p_name':'Tipos de rasgo', 'aliases':[
        'traittype', 'traittypes', 'trait type', 'trait types'
    ]}
]

def get_model_class(namestr):
    #global model_classes
    for i in model_classes:
        if namestr.lower() in [i['s_name'].lower(), i['p_name'].lower(), *i['aliases']]:
            return i
    return None

type_names = {
    int: 'Número entero',
    str: 'Texto'    
}